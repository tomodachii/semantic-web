"""Find Wikidata and DBpedia identity links for our movies, keeping the evidence for review."""

import argparse
import csv
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests
from rdflib import Graph, URIRef
from rdflib.namespace import OWL

from transform import DEFAULT_BASE_URI, PROJECT_DIR, read_csv, uri

WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
USER_AGENT = "semantic-web-movie-linker/1.0 (educational project)"
FIELDNAMES = [
    "local_uri", "tmdb_id", "title", "release_date",
    "wikidata_uri", "wikidata_label", "wikidata_years", "wikidata_imdb_id",
    "dbpedia_uri", "search_method", "matched_by", "score", "status",
]


def sparql_string(value: str) -> str:
    """Escape a value for a SPARQL string literal."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", " ")
    return f'"{escaped}"'


def query_wikidata(query: str, session: requests.Session, retries: int = 3) -> list[dict[str, str]]:
    """Run a SPARQL query, backing off when Wikidata throttles or times out."""
    for attempt in range(retries):
        try:
            response = session.get(
                WIKIDATA_SPARQL, params={"query": query, "format": "json"}, timeout=60
            )
            if response.status_code in (429, 502, 503, 504) and attempt < retries - 1:
                time.sleep(float(response.headers.get("Retry-After", 2 ** (attempt + 1))))
                continue
            response.raise_for_status()
            return [
                {key: value["value"] for key, value in binding.items()}
                for binding in response.json()["results"]["bindings"]
            ]
        except requests.Timeout:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** (attempt + 1))
    return []


def candidate_query(pattern: str) -> str:
    """Wrap a matching pattern with the facts we keep as evidence."""
    return f"""
        SELECT ?item ?label ?imdb ?date ?enwiki WHERE {{
            {pattern}
            OPTIONAL {{ ?item rdfs:label ?label . FILTER(LANG(?label) IN ("en", "mul")) }}
            OPTIONAL {{ ?item wdt:P345 ?imdb . }}
            OPTIONAL {{ ?item wdt:P577 ?date . }}
            OPTIONAL {{ ?article schema:about ?item ;
                                 schema:isPartOf <https://en.wikipedia.org/> ;
                                 schema:name ?enwiki . }}
        }}
    """


def merge_candidates(rows: list[dict[str, str]]) -> list[dict]:
    """Collapse the label/date/IMDb/article cross product into one record per Wikidata item."""
    items: dict[str, dict] = {}
    for row in rows:
        candidate = items.setdefault(
            row["item"],
            {"item": row["item"], "label": "", "imdb": set(), "years": set(), "enwiki": ""},
        )
        candidate["label"] = row.get("label", candidate["label"])
        candidate["enwiki"] = row.get("enwiki", candidate["enwiki"])
        if row.get("imdb"):
            candidate["imdb"].add(row["imdb"])
        if year := year_of(row.get("date")):
            candidate["years"].add(year)
    return list(items.values())


def identifier_candidates(tmdb_id: str, session: requests.Session) -> list[dict]:
    """Wikidata items carrying this TMDB movie ID (P4947)."""
    pattern = f"?item wdt:P4947 {sparql_string(tmdb_id)} ."
    return merge_candidates(query_wikidata(candidate_query(pattern), session))


def title_candidates(title: str, session: requests.Session) -> list[dict]:
    """Wikidata films (Q11424 or a subclass) whose label (English or shared 'mul') equals the title."""
    pattern = f"""
        VALUES ?title {{ {sparql_string(title)}@en {sparql_string(title)}@mul }}
        ?item rdfs:label ?title ;
              wdt:P31/wdt:P279* wd:Q11424 ;
              wdt:P577 [] .
    """
    return merge_candidates(query_wikidata(candidate_query(pattern), session))


def year_of(value: str | None) -> str | None:
    """Return the four-digit year at the start of an ISO date, or None."""
    value = (value or "").strip().lstrip("+")
    return value[:4] if value[:4].isdigit() else None


def years_apart(local_year: str, years: set[str]) -> int:
    """Smallest distance in years between the local year and any Wikidata release year."""
    return min(abs(int(local_year) - int(year)) for year in years)


def dbpedia_uri(enwiki_title: str) -> str:
    """DBpedia resource IRI for an English Wikipedia article title.

    DBpedia keeps non-ASCII letters as they are (Zoe_Saldaña), so only ASCII is percent-encoded.
    """
    title = enwiki_title.replace(" ", "_")
    return "http://dbpedia.org/resource/" + "".join(
        char if ord(char) > 127 else quote(char, safe="_()!':,-") for char in title
    )


def score_candidate(movie: dict[str, str], candidate: dict, method: str) -> tuple[float, str]:
    """Score one candidate. Only an ID match with the same release year reaches 1.0."""
    prefix = "tmdb_id" if method == "identifier" else "title"
    local_year = year_of(movie["release_date"])
    if not local_year or not candidate["years"]:
        return 0.5, f"{prefix}+release_year_missing"

    gap = years_apart(local_year, candidate["years"])
    if gap == 0:
        return (1.0 if method == "identifier" else 0.9), f"{prefix}+release_year"
    if gap == 1:
        # Wikidata keeps festival and per-country dates, so one year apart is not a contradiction.
        return (0.7 if method == "identifier" else 0.6), f"{prefix}+release_year_near"
    return 0.0, f"{prefix}+release_year_mismatch"


def status_of(score: float, matched_by: str) -> str:
    if score == 1.0:
        return "approved"
    if "release_year_mismatch" in matched_by:
        return "rejected"
    return "review"


def local_movies(data_dir: Path, base_uri: str) -> list[dict[str, str]]:
    """Movies from data/prepared/movies.csv, with the same URIs transform.py gives them."""
    return [
        {
            "local_uri": str(uri(base_uri, "movie", row["id"])),
            "tmdb_id": row["id"],
            "title": (row.get("title") or "").strip(),
            "release_date": (row.get("release_date") or "").strip(),
        }
        for row in read_csv(data_dir, "movies.csv")
    ]


def movie_rows(movie: dict[str, str], session: requests.Session) -> list[dict[str, str]]:
    """Candidate rows for one movie: search by TMDB ID first, then by title."""
    method = "identifier"
    candidates = identifier_candidates(movie["tmdb_id"], session)
    if not candidates and movie["title"]:
        method = "title+release_year"
        candidates = [
            candidate
            for candidate in title_candidates(movie["title"], session)
            if not movie["release_date"]
            or not candidate["years"]
            or years_apart(year_of(movie["release_date"]), candidate["years"]) <= 1
        ]

    base = {key: movie[key] for key in ("local_uri", "tmdb_id", "title", "release_date")}
    if not candidates:
        return [{**dict.fromkeys(FIELDNAMES, ""), **base,
                 "search_method": method, "matched_by": "no_candidate", "score": "0.00",
                 "status": "not_found"}]

    rows = []
    for candidate in candidates:
        score, matched_by = score_candidate(movie, candidate, "identifier" if method == "identifier" else "title")
        rows.append({
            **base,
            "wikidata_uri": candidate["item"],
            "wikidata_label": candidate["label"],
            "wikidata_years": "|".join(sorted(candidate["years"])),
            "wikidata_imdb_id": "|".join(sorted(candidate["imdb"])),
            "dbpedia_uri": dbpedia_uri(candidate["enwiki"]) if candidate["enwiki"] else "",
            "search_method": method,
            "matched_by": matched_by,
            "score": f"{score:.2f}",
            "status": status_of(score, matched_by),
        })

    approved = [row for row in rows if row["status"] == "approved"]
    if len(approved) > 1:
        # Two items claim the same TMDB ID: a human must decide which one is the film.
        for row in approved:
            row["status"] = "review"
            row["matched_by"] += "+ambiguous"
    return rows


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


def link_movies(data_dir: Path, base_uri: str, candidates_path: Path, links_path: Path,
                delay: float, limit: int | None = None) -> tuple[list[dict[str, str]], Graph]:
    movies = local_movies(data_dir, base_uri)[:limit]
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    rows: list[dict[str, str]] = []
    for number, movie in enumerate(movies, start=1):
        movie_result = movie_rows(movie, session)
        rows.extend(movie_result)
        statuses = ",".join(sorted({row["status"] for row in movie_result}))
        print(f"[{number}/{len(movies)}] {movie['title']} ({movie['release_date'][:4]}): {statuses}",
              file=sys.stderr)
        time.sleep(delay)

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
    parser = argparse.ArgumentParser(description="Link our movies to Wikidata and DBpedia.")
    parser.add_argument("--data-dir", type=Path, default=PROJECT_DIR / "data/prepared")
    parser.add_argument("--base-uri", default=DEFAULT_BASE_URI)
    parser.add_argument("--candidates", type=Path, default=PROJECT_DIR / "output/movie_candidates.csv")
    parser.add_argument("--links", type=Path, default=PROJECT_DIR / "output/movie_links.ttl")
    parser.add_argument("--delay", type=float, default=0.2, help="seconds between movies")
    parser.add_argument("--limit", type=int, help="only link the first N movies (for a trial run)")
    args = parser.parse_args()

    try:
        rows, graph = link_movies(
            args.data_dir, args.base_uri, args.candidates, args.links, max(args.delay, 0), args.limit
        )
    except (OSError, requests.RequestException, KeyError, ValueError) as error:
        parser.error(str(error))
    print(f"Created {args.candidates} with {len(rows)} candidate rows.")
    print(f"Created {args.links} with {len(graph)} approved link triples.")


if __name__ == "__main__":
    main()
