"""Convert prepared TMDB CSV tables to RDF/Turtle."""

import argparse
import hashlib
from datetime import date
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote, urlsplit

from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef, XSD
from tmdb import TABLE_FIELDS, number, read_csv

PROJECT_DIR = Path(__file__).resolve().parents[1]
SCHEMA = Namespace("https://schema.org/")


def build_graph(data_dir, base_uri="https://example.org/"):
    """Validate the prepared tables and return an RDF graph."""
    parsed = urlsplit(base_uri)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.query or parsed.fragment:
        raise ValueError("base-uri must be an absolute HTTP(S) URI without query or fragment")
    base_uri = base_uri.rstrip("/") + "/"
    kg = Namespace(base_uri + "ontology/")
    graph = Graph()
    for prefix, ns in [("schema", SCHEMA), ("kg", kg), ("rdf", RDF), ("rdfs", RDFS), ("xsd", XSD)]:
        graph.bind(prefix, ns)
    tables = {name: read_csv(Path(data_dir) / f"{name}.csv", fields)
              for name, fields in TABLE_FIELDS.items()}

    def uri(kind, identifier):
        return URIRef(base_uri + kind + "/" + quote(identifier, safe=""))

    def literal(subject, predicate, value, datatype=None):
        if value != "":
            graph.add((subject, predicate, Literal(value, datatype=datatype)))

    def numeric(subject, predicate, value, integer=False):
        if value != "":
            cleaned = number(value, str(predicate), integer=integer)
            literal(subject, predicate, int(cleaned) if integer else Decimal(cleaned),
                    XSD.integer if integer else XSD.decimal)

    # Reject relationships pointing to undeclared entities.
    entities = {}
    definitions = [
        ("movies", "id", "movie", SCHEMA.Movie),
        ("people", "id", "person", SCHEMA.Person),
        ("genres", "id", "genre", kg.Genre),
        ("companies", "id", "company", SCHEMA.Organization),
        ("countries", "country_code", "country", SCHEMA.Country),
        ("languages", "language_code", "language", SCHEMA.Language),
    ]
    for table, key, kind, rdf_type in definitions:
        entities[table] = {}
        for row in tables[table]:
            identifier = row[key]
            if not identifier or identifier in entities[table]:
                raise ValueError(f"{table}.csv: empty or duplicate identifier {identifier!r}")
            node = uri(kind, identifier)
            entities[table][identifier] = node
            graph.add((node, RDF.type, rdf_type))
            literal(node, SCHEMA.identifier, identifier)
            literal(node, SCHEMA.name, row["title"] if table == "movies" else row["name"])

    def reference(table, identifier):
        if identifier not in entities[table]:
            raise ValueError(f"Unknown {table} identifier: {identifier!r}")
        return entities[table][identifier]

    for row in tables["movies"]:
        movie = reference("movies", row["id"])
        literal(movie, kg.originalTitle, row["original_title"])
        literal(movie, SCHEMA.abstract, row["overview"])
        literal(movie, kg.status, row["status"])
        if row["release_date"]:
            literal(movie, SCHEMA.datePublished, date.fromisoformat(row["release_date"]), XSD.date)
        if row["runtime"]:
            minutes = number(row["runtime"], "runtime", integer=True)
            literal(movie, SCHEMA.duration, f"PT{minutes}M", XSD.duration)
        numeric(movie, kg.budgetUSD, row["budget"], integer=True)
        numeric(movie, kg.revenueUSD, row["revenue"], integer=True)
        if row["original_language"]:
            graph.add((movie, kg.originalLanguage, reference("languages", row["original_language"])))
        if row["vote_average"] or row["vote_count"]:
            rating = uri("rating", row["id"])
            graph.add((movie, SCHEMA.aggregateRating, rating))
            graph.add((rating, RDF.type, SCHEMA.AggregateRating))
            numeric(rating, SCHEMA.ratingValue, row["vote_average"])
            numeric(rating, SCHEMA.ratingCount, row["vote_count"], integer=True)
            if row["vote_average"]:
                numeric(rating, SCHEMA.bestRating, "10")
                numeric(rating, SCHEMA.worstRating, "0")
        # The TMDB page is a reference, not an entity-equivalence assertion.
        graph.add((movie, RDFS.seeAlso, URIRef("https://www.themoviedb.org/movie/" + quote(row["id"], safe=""))))

    relationships = [
        ("movie_genres", "genre_id", "genres", kg.hasGenre),
        ("movie_companies", "company_id", "companies", SCHEMA.productionCompany),
        ("movie_countries", "country_code", "countries", SCHEMA.countryOfOrigin),
        ("movie_languages", "language_code", "languages", SCHEMA.inLanguage),
    ]
    for table, key, target, predicate in relationships:
        for row in tables[table]:
            graph.add((reference("movies", row["movie_id"]), predicate, reference(target, row[key])))

    # Jobs and characters belong to a credit, rather than globally to a person.
    credits = {}
    for table, credit_type, predicate in [
        ("cast", kg.CastCredit, kg.hasCastCredit), ("crew", kg.CrewCredit, kg.hasCrewCredit),
    ]:
        for row in tables[table]:
            movie = reference("movies", row["movie_id"])
            person = reference("people", row["person_id"])
            payload = tuple(row[field] for field in TABLE_FIELDS[table])
            fallback = hashlib.sha256(repr(payload).encode("utf-8")).hexdigest()
            identifier = row["movie_id"] + "-" + (row["credit_id"] or fallback)
            credit = uri(table + "-credit", identifier)
            if credit in credits and credits[credit] != payload:
                raise ValueError(f"{table}.csv: conflicting credit {identifier!r}")
            credits[credit] = payload
            graph.add((movie, predicate, credit))
            graph.add((credit, RDF.type, credit_type))
            graph.add((credit, kg.person, person))
            literal(credit, kg.sourceCreditId, row["credit_id"])
            if table == "cast":
                graph.add((movie, SCHEMA.actor, person))
                literal(credit, SCHEMA.characterName, row["character"])
                numeric(credit, SCHEMA.position, row["order"], integer=True)
            else:
                literal(credit, SCHEMA.roleName, row["job"])
                literal(credit, kg.department, row["department"])
                roles = {"Director": SCHEMA.director, "Producer": SCHEMA.producer,
                         "Writer": SCHEMA.author, "Screenplay": SCHEMA.author}
                graph.add((movie, roles.get(row["job"], SCHEMA.contributor), person))
    return graph


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=PROJECT_DIR / "data")
    parser.add_argument("--output", type=Path, default=PROJECT_DIR / "output" / "movies.ttl")
    parser.add_argument("--base-uri", default="https://example.org/",
                        help="Public entity URI prefix; default is a development placeholder")
    args = parser.parse_args()
    try:
        graph = build_graph(args.data_dir, args.base_uri)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(args.output), format="turtle")
    print(f"Wrote {len(graph):,} triples to {args.output}")


if __name__ == "__main__":
    main()
