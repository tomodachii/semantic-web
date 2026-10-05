"""Prepare movie tables from the two TMDB 5000 CSV files downloaded from Kaggle."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
CREW_JOBS = {"Director", "Writer", "Screenplay", "Producer"}
MOVIE_FIELDS = [
    "id", "title", "original_title", "overview", "original_language",
    "release_date", "runtime", "vote_average", "vote_count", "budget",
    "revenue", "status",
]
TABLE_FIELDS = {
    "movies": MOVIE_FIELDS,
    "people": ["id", "name"],
    "cast": ["movie_id", "person_id", "person_name", "character", "order", "credit_id"],
    "crew": ["movie_id", "person_id", "person_name", "job", "department", "credit_id"],
    "genres": ["id", "name"],
    "companies": ["id", "name"],
    "countries": ["country_code", "name"],
    "languages": ["language_code", "name"],
    "movie_genres": ["movie_id", "genre_id"],
    "movie_companies": ["movie_id", "company_id"],
    "movie_countries": ["movie_id", "country_code"],
    "movie_languages": ["movie_id", "language_code"],
}


def text(value):
    """Trim surrounding whitespace without changing names or internal spaces."""
    return "" if value is None else str(value).strip()


def number(value, field, *, integer=False, zero_is_missing=False):
    """Keep missing values empty and reject invalid or negative numbers."""
    value = text(value)
    if not value:
        return ""
    try:
        result = Decimal(value)
    except InvalidOperation:
        raise ValueError(f"Invalid {field}: {value!r}") from None
    if not result.is_finite() or result < 0:
        raise ValueError(f"Invalid {field}: {value!r}")
    if integer and result != result.to_integral_value():
        raise ValueError(f"Expected an integer for {field}: {value!r}")
    if zero_is_missing and result == 0:
        return ""
    return str(int(result)) if integer else format(result, "f")


def entity_id(value, field):
    result = number(value, field, integer=True, zero_is_missing=True)
    if not result:
        raise ValueError(f"Missing {field}")
    return result


def read_csv(path, required_fields):
    # Long crew lists can exceed the CSV module's default cell-size limit.
    csv.field_size_limit(10_000_000)
    with path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        missing = set(required_fields) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path.name}: missing columns: {', '.join(sorted(missing))}")
        return list(reader)


def json_list(value, field):
    """Kaggle stores lists of objects as JSON inside CSV cells."""
    if not text(value):
        return []
    try:
        items = json.loads(value)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in {field}") from None
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        raise ValueError(f"Expected a JSON list of objects in {field}")
    return items


def index_rows(rows, id_column, source_name, stats):
    """Join by movie ID; titles are not unique identifiers."""
    indexed = {}
    for row in rows:
        movie_id = entity_id(row[id_column], f"{source_name}.{id_column}")
        if movie_id in indexed:
            if indexed[movie_id] != row:
                raise ValueError(f"Conflicting duplicate movie ID {movie_id} in {source_name}")
            stats[f"duplicate_{source_name}_rows"] += 1
        else:
            indexed[movie_id] = row
    return indexed


def prepare_tables(movies_path, credits_path, limit=100, cast_limit=10):
    """Build all tables before writing so invalid input does not leave partial CSVs."""
    stats = Counter()
    nested_fields = ["genres", "production_companies", "production_countries", "spoken_languages"]
    movie_rows = read_csv(movies_path, MOVIE_FIELDS + nested_fields)
    credit_rows = read_csv(credits_path, ["movie_id", "cast", "crew"])
    movies = index_rows(movie_rows, "id", "movies", stats)
    credits = index_rows(credit_rows, "movie_id", "credits", stats)
    selected = list(movies.items())
    if limit:
        selected = selected[:limit]

    tables = {name: [] for name in TABLE_FIELDS}
    # Lookup dictionaries share entities across films. Relationship sets remove duplicates.
    entities = {name: {} for name in ("people", "genres", "companies", "countries", "languages")}
    relations = {name: set() for name in ("movie_genres", "movie_companies", "movie_countries", "movie_languages")}

    for movie_id, source in selected:
        try:
            movie = {field: text(source[field]) for field in MOVIE_FIELDS}
            movie["id"] = movie_id
            if not movie["title"]:
                raise ValueError("Missing title")
            if movie["release_date"]:
                movie["release_date"] = date.fromisoformat(movie["release_date"]).isoformat()
            for field in ("runtime", "budget", "revenue", "vote_count"):
                movie[field] = number(source[field], field, integer=True,
                                      zero_is_missing=field != "vote_count")
            movie["vote_average"] = number(source["vote_average"], "vote_average")
            if movie["vote_average"] and Decimal(movie["vote_average"]) > 10:
                raise ValueError("vote_average must be between 0 and 10")
            # A rating without any votes is not a meaningful observed rating.
            if movie["vote_count"] in ("", "0"):
                movie["vote_average"] = ""
            tables["movies"].append(movie)

            # (source column, lookup table, source key, output key, relationship table)
            for source_field, table, source_key, output_key, relation in [
                ("genres", "genres", "id", "id", "movie_genres"),
                ("production_companies", "companies", "id", "id", "movie_companies"),
                ("production_countries", "countries", "iso_3166_1", "country_code", "movie_countries"),
                ("spoken_languages", "languages", "iso_639_1", "language_code", "movie_languages"),
            ]:
                for item in json_list(source[source_field], source_field):
                    key = entity_id(item.get(source_key), source_field) if source_key == "id" else text(item.get(source_key))
                    if not key:
                        raise ValueError(f"Missing code in {source_field}")
                    entities[table][key] = {output_key: key, "name": text(item.get("name"))}
                    relations[relation].add((movie_id, key))

            # Preserve the original language even if it is absent from spoken_languages.
            language = movie["original_language"]
            if language and language not in entities["languages"]:
                entities["languages"][language] = {"language_code": language, "name": ""}

            credit = credits.get(movie_id)
            if credit is None:
                stats["movies_without_credits"] += 1
                continue
            cast = json_list(credit["cast"], "cast")
            for person in cast:
                person["order"] = number(person.get("order"), "cast.order", integer=True)
            # Missing cast order goes last; zero is a valid first position.
            cast.sort(key=lambda person: int(person["order"]) if person["order"] else float("inf"))
            if cast_limit:
                cast = cast[:cast_limit]
            for person in cast:
                person_id = entity_id(person.get("id"), "cast.person_id")
                name = text(person.get("name"))
                entities["people"].setdefault(person_id, {"id": person_id, "name": name})
                tables["cast"].append({
                    "movie_id": movie_id, "person_id": person_id, "person_name": name,
                    "character": text(person.get("character")), "order": person["order"],
                    "credit_id": text(person.get("credit_id")),
                })
            for person in json_list(credit["crew"], "crew"):
                job = text(person.get("job"))
                if job not in CREW_JOBS:
                    continue
                person_id = entity_id(person.get("id"), "crew.person_id")
                name = text(person.get("name"))
                entities["people"].setdefault(person_id, {"id": person_id, "name": name})
                tables["crew"].append({
                    "movie_id": movie_id, "person_id": person_id, "person_name": name,
                    "job": job, "department": text(person.get("department")),
                    "credit_id": text(person.get("credit_id")),
                })
        except ValueError as error:
            raise ValueError(f"Movie {movie_id}: {error}") from error

    for table, records in entities.items():
        tables[table] = list(records.values())
    for table, pairs in relations.items():
        fields = TABLE_FIELDS[table]
        tables[table] = [dict(zip(fields, pair)) for pair in sorted(pairs)]
    for table in ("cast", "crew"):
        fields = TABLE_FIELDS[table]
        unique = {tuple(row[field] for field in fields): row for row in tables[table]}
        stats[f"duplicate_{table}_rows"] = len(tables[table]) - len(unique)
        tables[table] = list(unique.values())

    summary = {
        "source_movie_rows": len(movie_rows), "source_credit_rows": len(credit_rows),
        "unique_source_movies": len(movies), "selected_movies": len(selected),
        "limit": limit, "cast_limit": cast_limit, "crew_jobs": sorted(CREW_JOBS),
        "cleaning_counts": dict(stats),
        "output_rows": {f"{name}.csv": len(rows) for name, rows in tables.items()},
        "missing_movie_fields": {field: sum(row[field] == "" for row in tables["movies"])
                                 for field in MOVIE_FIELDS},
    }
    return tables, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=PROJECT_DIR / "data" / "raw")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_DIR / "data")
    parser.add_argument("--limit", type=int, default=100, help="Number of films in source order; 0 keeps all films.")
    parser.add_argument("--cast-limit", type=int, default=10, help="Number of actors per film; 0 keeps the full cast.")
    args = parser.parse_args()
    if args.limit < 0 or args.cast_limit < 0:
        parser.error("--limit and --cast-limit must be non-negative")
    movies_path = args.input_dir / "tmdb_5000_movies.csv"
    credits_path = args.input_dir / "tmdb_5000_credits.csv"
    try:
        tables, summary = prepare_tables(movies_path, credits_path, args.limit, args.cast_limit)
        summary["processed_at_utc"] = datetime.now(timezone.utc).isoformat()
        summary["source_url"] = "https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata"
        summary["input_files"] = [
            {"path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in (movies_path, credits_path)
        ]
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name, rows in tables.items():
            path = args.output_dir / f"{name}.csv"
            with path.open("w", newline="", encoding="utf-8") as output:
                writer = csv.DictWriter(output, fieldnames=TABLE_FIELDS[name])
                writer.writeheader()
                writer.writerows(rows)
            print(f"Created {path.name}: {len(rows)} rows")
        summary_path = args.output_dir / "preparation_summary.json"
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Created {summary_path.name}")
    except (OSError, ValueError, csv.Error) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
