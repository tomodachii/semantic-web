"""Find Wikidata and DBpedia identity links for our people (cast and directors), keeping the evidence."""

import argparse
import csv
import sys
import time
import unicodedata
from pathlib import Path

import requests
from rdflib import Graph, URIRef
from rdflib.namespace import OWL

from link_movies import USER_AGENT, dbpedia_uri, query_wikidata, sparql_string
from transform import DEFAULT_BASE_URI, PROJECT_DIR, read_csv, uri

WIKIDATA_ENTITY = "http://www.wikidata.org/entity/"
BATCH_SIZE = 50
FIELDNAMES = [
    "local_uri", "tmdb_person_id", "name", "roles", "movie_count",
    "wikidata_uri", "wikidata_label", "wikidata_imdb_id", "dbpedia_uri",
    "search_method", "matched_by", "score", "status",
]


def normalize(name: str) -> str:
    """Casefold, drop accents and punctuation so 'Zoë Saldaña' equals 'Zoe Saldana'."""
    decomposed = unicodedata.normalize("NFKD", name)
    letters = "".join(char if char.isalnum() else " " for char in decomposed if not unicodedata.combining(char))
    return " ".join(letters.casefold().split())


def local_people(data_dir: Path, base_uri: str) -> list[dict]:
    """Unique people from cast.csv and crew.csv, with their roles and movie ids."""
    people: dict[str, dict] = {}
    for filename, role_of in (("cast.csv", lambda row: "cast"), ("crew.csv", lambda row: row["job"].strip().lower())):
        for row in read_csv(data_dir, filename):
            person = people.setdefault(
                row["person_id"],
                {"local_uri": str(uri(base_uri, "person", row["person_id"])), "tmdb_person_id": row["person_id"],
                 "name": "", "roles": set(), "movies": set()},
            )
            person["name"] = person["name"] or (row.get("person_name") or "").strip()
            person["roles"].add(role_of(row))
            person["movies"].add(row["movie_id"])
    return list(people.values())


def linked_films(movie_links: Path | None, base_uri: str) -> dict[str, set[str]]:
    """Local movie id -> Wikidata film items, from the approved links of link_movies.py."""
    if not movie_links or not movie_links.is_file():
        return {}
    prefix = f"{base_uri.rstrip('/')}/movie/"
    films: dict[str, set[str]] = {}
    for local, _, remote in Graph().parse(movie_links, format="turtle").triples((None, OWL.sameAs, None)):
        if str(local).startswith(prefix) and str(remote).startswith(WIKIDATA_ENTITY):
            films.setdefault(str(local)[len(prefix):], set()).add(str(remote))
    return films


def merge_candidates(rows: list[dict[str, str]]) -> list[dict]:
    """Collapse the label/alias/IMDb/article cross product into one record per Wikidata item."""
    items: dict[str, dict] = {}
    for row in rows:
        candidate = items.setdefault(
            row["item"],
            {"item": row["item"], "label": "", "names": set(), "imdb": set(), "human": False,
             "enwiki": "", "tmdb": set()},
        )
        candidate["label"] = row.get("label", candidate["label"])
        candidate["enwiki"] = row.get("enwiki", candidate["enwiki"])
        candidate["human"] = candidate["human"] or row.get("human") == "true"
        for key, field in (("label", "names"), ("alias", "names"), ("imdb", "imdb"), ("tmdb", "tmdb")):
            if row.get(key):
                candidate[field].add(row[key])
    return list(items.values())


CANDIDATE_TAIL = """
    OPTIONAL { ?item rdfs:label ?label . FILTER(LANG(?label) IN ("en", "mul")) }
    OPTIONAL { ?item skos:altLabel ?alias . FILTER(LANG(?alias) IN ("en", "mul")) }
    OPTIONAL { ?item wdt:P345 ?imdb . }
    OPTIONAL { ?article schema:about ?item ;
                        schema:isPartOf <https://en.wikipedia.org/> ;
                        schema:name ?enwiki . }
    BIND(EXISTS { ?item wdt:P31 wd:Q5 } AS ?human)
"""


def identifier_candidates(tmdb_ids: list[str], session: requests.Session) -> list[dict]:
    """Wikidata items carrying one of these TMDB person IDs (P4985)."""
    values = " ".join(sparql_string(value) for value in tmdb_ids)
    query = f"""
        SELECT ?item ?tmdb ?label ?alias ?imdb ?enwiki ?human WHERE {{
            VALUES ?tmdb {{ {values} }}
            ?item wdt:P4985 ?tmdb .
            {CANDIDATE_TAIL}
        }}
    """
    return merge_candidates(query_wikidata(query, session))


def name_candidates(name: str, films: set[str], session: requests.Session) -> list[dict]:
    """Items labelled with this name (English or shared 'mul' label) that are cast (P161) or director (P57) of our linked films."""
    values = " ".join(f"wd:{film.rsplit('/', 1)[-1]}" for film in sorted(films))
    query = f"""
        SELECT ?item ?label ?alias ?imdb ?enwiki ?human WHERE {{
            VALUES ?film {{ {values} }}
            VALUES ?name {{ {sparql_string(name)}@en {sparql_string(name)}@mul }}
            ?item rdfs:label ?name .
            ?film wdt:P161|wdt:P57 ?item .
            {CANDIDATE_TAIL}
        }}
    """
    return merge_candidates(query_wikidata(query, session))


def score_candidate(person: dict, candidate: dict, method: str) -> tuple[float, str]:
    """Only a TMDB person ID match, a human item, and a matching name reach 1.0."""
    prefix = "tmdb_person_id" if method == "identifier" else "name+filmography"
    if not candidate["human"]:
        return 0.0, f"{prefix}+not_human"
    names_match = normalize(person["name"]) in {normalize(name) for name in candidate["names"]}
    if method == "identifier":
        return (1.0, f"{prefix}+name") if names_match else (0.7, f"{prefix}+name_differs")
    return 0.9, prefix


def status_of(score: float, matched_by: str) -> str:
    if score == 1.0:
        return "approved"
    if "not_human" in matched_by:
        return "rejected"
    return "review"


def candidate_row(person: dict, candidate: dict | None, method: str) -> dict[str, str]:
    base = {
        "local_uri": person["local_uri"], "tmdb_person_id": person["tmdb_person_id"], "name": person["name"],
        "roles": "|".join(sorted(person["roles"])), "movie_count": str(len(person["movies"])),
    }
    if candidate is None:
        return {**dict.fromkeys(FIELDNAMES, ""), **base,
                "search_method": method, "matched_by": "no_candidate", "score": "0.00", "status": "not_found"}
    score, matched_by = score_candidate(person, candidate, method)
    return {
        **base,
        "wikidata_uri": candidate["item"],
        "wikidata_label": candidate["label"],
        "wikidata_imdb_id": "|".join(sorted(candidate["imdb"])),
        "dbpedia_uri": dbpedia_uri(candidate["enwiki"]) if candidate["enwiki"] else "",
        "search_method": method,
        "matched_by": matched_by,
        "score": f"{score:.2f}",
        "status": status_of(score, matched_by),
    }


def demote_ambiguous(rows: list[dict[str, str]]) -> None:
    """A person with two approved items, or an item claimed by two people, needs a human decision."""
    approved = [row for row in rows if row["status"] == "approved"]
    counts = {key: {} for key in ("local_uri", "wikidata_uri")}
    for row in approved:
        for key, seen in counts.items():
            seen[row[key]] = seen.get(row[key], 0) + 1
    for row in approved:
        if any(counts[key][row[key]] > 1 for key in counts):
            row["status"] = "review"
            row["matched_by"] += "+ambiguous"


def link_graph(rows: list[dict[str, str]]) -> Graph:
    """owl:sameAs triples for approved rows only."""
    graph = Graph()
    graph.bind("owl", OWL)
    for row in rows:
        if row["status"] != "approved":
            continue
        local = URIRef(row["local_uri"])
        graph.add((local, OWL.sameAs, URIRef(row["wikidata_uri"])))
        if row["dbpedia_uri"]:
            graph.add((local, OWL.sameAs, URIRef(row["dbpedia_uri"])))
    return graph


def link_people(data_dir: Path, base_uri: str, movie_links: Path | None, candidates_path: Path,
                links_path: Path, delay: float, limit: int | None = None) -> tuple[list[dict[str, str]], Graph]:
    people = local_people(data_dir, base_uri)[:limit]
    films = linked_films(movie_links, base_uri)
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    found: dict[str, list[dict]] = {}
    for start in range(0, len(people), BATCH_SIZE):
        batch = people[start:start + BATCH_SIZE]
        for candidate in identifier_candidates([person["tmdb_person_id"] for person in batch], session):
            for tmdb_id in candidate["tmdb"]:
                found.setdefault(tmdb_id, []).append(candidate)
        print(f"ID lookup: {min(start + BATCH_SIZE, len(people))}/{len(people)} people", file=sys.stderr)
        time.sleep(delay)

    rows: list[dict[str, str]] = []
    for number, person in enumerate(people, start=1):
        method = "identifier"
        candidates = found.get(person["tmdb_person_id"], [])
        person_films = set().union(*(films.get(movie_id, set()) for movie_id in person["movies"]))
        if not candidates and person["name"] and person_films:
            method = "name+filmography"
            candidates = name_candidates(person["name"], person_films, session)
            time.sleep(delay)
            print(f"[{number}/{len(people)}] name fallback: {person['name']} -> {len(candidates)}", file=sys.stderr)
        rows.extend(candidate_row(person, candidate, method) for candidate in candidates or [None])

    demote_ambiguous(rows)

    candidates_path.parent.mkdir(parents=True, exist_ok=True)
    with candidates_path.open("w", newline="", encoding="utf-8-sig") as output:
        writer = csv.DictWriter(output, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    graph = link_graph(rows)
    links_path.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=links_path, format="turtle")
    return rows, graph


def main() -> None:
    parser = argparse.ArgumentParser(description="Link our people to Wikidata and DBpedia.")
    parser.add_argument("--data-dir", type=Path, default=PROJECT_DIR / "data/prepared")
    parser.add_argument("--base-uri", default=DEFAULT_BASE_URI)
    parser.add_argument("--movie-links", type=Path, default=PROJECT_DIR / "output/movie_links.ttl",
                        help="approved movie links from link_movies.py, used for the name fallback")
    parser.add_argument("--candidates", type=Path, default=PROJECT_DIR / "output/person_candidates.csv")
    parser.add_argument("--links", type=Path, default=PROJECT_DIR / "output/person_links.ttl")
    parser.add_argument("--delay", type=float, default=0.2, help="seconds between requests")
    parser.add_argument("--limit", type=int, help="only link the first N people (for a trial run)")
    args = parser.parse_args()

    try:
        rows, graph = link_people(args.data_dir, args.base_uri, args.movie_links, args.candidates,
                                  args.links, max(args.delay, 0), args.limit)
    except (OSError, requests.RequestException, KeyError, ValueError) as error:
        parser.error(str(error))
    print(f"Created {args.candidates} with {len(rows)} candidate rows.")
    print(f"Created {args.links} with {len(graph)} approved link triples.")


if __name__ == "__main__":
    main()
