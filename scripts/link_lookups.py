"""Find Wikidata and DBpedia links for our lookup tables: countries, languages and genres."""

import argparse
import csv
from pathlib import Path

import requests
from rdflib import Graph, URIRef
from rdflib.namespace import OWL, SKOS

from link_movies import USER_AGENT, dbpedia_uri, query_wikidata, sparql_string
from transform import DEFAULT_BASE_URI, PROJECT_DIR, read_csv, uri

FIELDNAMES = [
    "class", "local_uri", "key", "name", "wikidata_uri", "wikidata_label", "dbpedia_uri",
    "relation", "search_method", "matched_by", "status",
]
# Country and language codes are unique identifiers, so those links are identity links.
# Genres are matched by name, and TMDB's genre is not exactly Wikidata's, so they get a weaker relation.
LOOKUPS = {
    "country": {"file": "countries.csv", "key": "country_code", "property": "P297", "relation": OWL.sameAs},
    "language": {"file": "languages.csv", "key": "language_code", "property": "P218", "relation": OWL.sameAs},
    "genre": {"file": "genres.csv", "key": "id", "relation": SKOS.closeMatch},
}
# Wikidata names most film genres "<name> film" in lower case; these are the exceptions.
GENRE_SYNONYMS = {"Animation": ["animated film"]}

CANDIDATE_TAIL = """
    OPTIONAL { ?item rdfs:label ?label . FILTER(LANG(?label) IN ("en", "mul")) }
    OPTIONAL { ?article schema:about ?item ;
                        schema:isPartOf <https://en.wikipedia.org/> ;
                        schema:name ?enwiki . }
"""


def genre_variants(name: str) -> list[str]:
    """Labels a Wikidata film genre might carry for one of our genre names."""
    variants = [f"{name} film", f"{name.lower()} film", *GENRE_SYNONYMS.get(name, [])]
    return list(dict.fromkeys(variants))


def merge_candidates(rows: list[dict[str, str]], key_field: str) -> dict[str, list[dict]]:
    """Group query rows by lookup key, then collapse them to one record per Wikidata item."""
    grouped: dict[str, dict[str, dict]] = {}
    for row in rows:
        item = grouped.setdefault(row[key_field], {}).setdefault(
            row["item"], {"item": row["item"], "label": "", "enwiki": ""}
        )
        item["label"] = row.get("label", item["label"])
        item["enwiki"] = row.get("enwiki", item["enwiki"])
    return {key: list(items.values()) for key, items in grouped.items()}


def code_candidates(codes: list[str], wikidata_property: str, session: requests.Session) -> dict[str, list[dict]]:
    """Items whose ISO code property equals one of our codes (P297 country, P218 language)."""
    values = " ".join(sparql_string(code) for code in codes)
    query = f"""
        SELECT ?code ?item ?label ?enwiki WHERE {{
            VALUES ?code {{ {values} }}
            ?item wdt:{wikidata_property} ?code .
            {CANDIDATE_TAIL}
        }}
    """
    return merge_candidates(query_wikidata(query, session), "code")


def genre_candidates(variants: dict[str, str], session: requests.Session) -> dict[str, list[dict]]:
    """Film genres (Q201658 or a subclass) labelled with one of the variants; keyed by our genre id."""
    by_label = {variant.casefold(): key for variant, key in variants.items()}
    values = " ".join(f"{sparql_string(variant)}@en" for variant in variants)
    query = f"""
        SELECT ?name ?item ?label ?enwiki WHERE {{
            VALUES ?name {{ {values} }}
            ?item rdfs:label ?name ;
                  wdt:P31/wdt:P279* wd:Q201658 .
            {CANDIDATE_TAIL}
        }}
    """
    rows = [{**row, "genre": by_label[row["name"].casefold()]} for row in query_wikidata(query, session)]
    return merge_candidates(rows, "genre")


def candidate_rows(kind: str, local: dict[str, str], candidates: list[dict]) -> list[dict[str, str]]:
    """One row per candidate. Exactly one candidate is approved; several need a human."""
    lookup = LOOKUPS[kind]
    method = "name_variant" if kind == "genre" else f"iso_code_{lookup['property']}"
    base = {"class": kind, "local_uri": local["local_uri"], "key": local["key"], "name": local["name"],
            "relation": str(lookup["relation"]), "search_method": method}
    if not candidates:
        return [{**dict.fromkeys(FIELDNAMES, ""), **base, "matched_by": "no_candidate", "status": "not_found"}]

    status, matched_by = ("approved", "unique") if len(candidates) == 1 else ("review", "ambiguous")
    return [
        {**base,
         "wikidata_uri": candidate["item"],
         "wikidata_label": candidate["label"],
         "dbpedia_uri": dbpedia_uri(candidate["enwiki"]) if candidate["enwiki"] else "",
         "matched_by": matched_by,
         "status": status}
        for candidate in candidates
    ]


def link_graph(rows: list[dict[str, str]]) -> Graph:
    """Link triples for approved rows only, using each class's relation."""
    graph = Graph()
    graph.bind("owl", OWL)
    graph.bind("skos", SKOS)
    for row in rows:
        if row["status"] != "approved":
            continue
        local, relation = URIRef(row["local_uri"]), URIRef(row["relation"])
        graph.add((local, relation, URIRef(row["wikidata_uri"])))
        if row["dbpedia_uri"]:
            graph.add((local, relation, URIRef(row["dbpedia_uri"])))
    return graph


def link_lookups(data_dir: Path, base_uri: str, candidates_path: Path, links_path: Path) -> tuple[list[dict[str, str]], Graph]:
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    rows: list[dict[str, str]] = []
    for kind, lookup in LOOKUPS.items():
        table = [
            {"local_uri": str(uri(base_uri, kind, row[lookup["key"]])), "key": row[lookup["key"]],
             "name": (row.get("name") or "").strip()}
            for row in read_csv(data_dir, lookup["file"])
        ]
        if kind == "genre":
            variants = {variant: row["key"] for row in table for variant in genre_variants(row["name"])}
            found = genre_candidates(variants, session)
        else:
            found = code_candidates([row["key"] for row in table], lookup["property"], session)
        for local in table:
            rows.extend(candidate_rows(kind, local, found.get(local["key"], [])))

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
    parser = argparse.ArgumentParser(description="Link our countries, languages and genres to Wikidata and DBpedia.")
    parser.add_argument("--data-dir", type=Path, default=PROJECT_DIR / "data/prepared")
    parser.add_argument("--base-uri", default=DEFAULT_BASE_URI)
    parser.add_argument("--candidates", type=Path, default=PROJECT_DIR / "output/lookup_candidates.csv")
    parser.add_argument("--links", type=Path, default=PROJECT_DIR / "output/lookup_links.ttl")
    args = parser.parse_args()

    try:
        rows, graph = link_lookups(args.data_dir, args.base_uri, args.candidates, args.links)
    except (OSError, requests.RequestException, KeyError, ValueError) as error:
        parser.error(str(error))
    print(f"Created {args.candidates} with {len(rows)} candidate rows.")
    print(f"Created {args.links} with {len(graph)} approved link triples.")


if __name__ == "__main__":
    main()
