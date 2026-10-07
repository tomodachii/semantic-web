"""Split raw TMDB 5000 CSVs into 11 tables for movies, credits, genres, countries, languages, and keywords."""

import argparse
import csv
import json
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
MOVIE_FIELDS = [
    "id", "title", "overview", "original_language",
    "release_date", "runtime", "vote_average", "vote_count",
]
TABLE_FIELDS = {
    "movies": MOVIE_FIELDS,
    "genres": ["id", "name"],
    "movie_genres": ["movie_id", "genre_id"],
    "countries": ["country_code", "name"],
    "movie_countries": ["movie_id", "country_code"],
    "languages": ["language_code", "name"],
    "movie_languages": ["movie_id", "language_code"],
    "cast": ["movie_id", "person_id", "person_name", "character", "order"],
    "crew": ["movie_id", "person_id", "person_name", "job"],
    "keywords": ["id", "name"],
    "movie_keywords": ["movie_id", "keyword_id"],
}
NESTED_FIELDS = [
    "genres", "production_countries",
    "spoken_languages", "keywords",
]


def text(value):
    """Preserve Unicode and internal spaces; missing values become empty cells."""
    return "" if value is None else str(value).strip()


def number(value, field, integer=False):
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
    return str(int(result)) if integer else format(result, "f")


def identifier(value):
    value = number(value, "ID", integer=True)
    if not value or value == "0":
        raise ValueError("Missing or zero entity ID")
    return value


def read_rows(path, required):
    """Stream CSV rows; large nested crew cells can exceed Python's default limit."""
    csv.field_size_limit(10_000_000)
    with Path(path).open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        missing = set(required) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{Path(path).name}: missing columns: {', '.join(sorted(missing))}")
        yield from reader


def json_list(value, field):
    if not text(value):
        return []
    try:
        items = json.loads(value)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in {field}") from error
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        raise ValueError(f"Expected a list of objects in {field}")
    return items


def prepare_tables(movies_path, credits_path, limit=100, cast_limit=10):
    """Build tables in memory before writing; join credits by ID, never row order."""
    if limit < 0 or cast_limit < 0:
        raise ValueError("Limits must be nonnegative; 0 means all.")
    selected = {}
    required = [field for field in MOVIE_FIELDS] + NESTED_FIELDS
    for row in read_rows(movies_path, required):
        movie_id = identifier(row["id"])
        if movie_id in selected and selected[movie_id] != row:
            raise ValueError(f"Conflicting duplicate movie ID {movie_id}")
        selected[movie_id] = row
        if limit and len(selected) >= limit:
            break

    # Stream the credits file to find selected IDs even when files are reordered.
    # Keep only matching rows, and parse JSON only for those movies.
    credits = {}
    for row in read_rows(credits_path, ["movie_id", "cast", "crew"]):
        movie_id = identifier(row["movie_id"])
        if movie_id not in selected:
            continue
        if movie_id in credits and credits[movie_id] != row:
            raise ValueError(f"Conflicting duplicate credits for movie {movie_id}")
        credits[movie_id] = row

    tables = {name: [] for name in TABLE_FIELDS}
    entities = {name: {} for name in ["genres", "countries", "languages", "keywords"]}
    missing_credits = []

    def remember(table, key, record):
        """Reuse shared entities; reject conflicting nonempty source labels."""
        previous = entities[table].get(key)
        if previous:
            for field, value in record.items():
                if previous.get(field) and value and previous[field] != value:
                    raise ValueError(f"Conflicting {table} {key}: {field}")
            record = {field: record.get(field) or value for field, value in previous.items()}
        entities[table][key] = record

    for movie_id, source in selected.items():
        try:
            # Keep the available core movie fields; IMDb is absent in these raw files.
            movie = {field: text(source.get(field)) for field in MOVIE_FIELDS}
            movie["id"] = movie_id
            if not movie["title"]:
                raise ValueError("Missing title")
            if movie["release_date"]:
                movie["release_date"] = date.fromisoformat(movie["release_date"]).isoformat()
            movie["runtime"] = number(movie["runtime"], "runtime", integer=True)
            movie["vote_count"] = number(movie["vote_count"], "vote_count", integer=True)
            movie["vote_average"] = number(movie["vote_average"], "vote_average")
            if movie["vote_average"] and Decimal(movie["vote_average"]) > 10:
                raise ValueError("vote_average must be between 0 and 10")
            tables["movies"].append(movie)

            # Each nested list produces an entity lookup and movie–entity pairs.
            for field, table, source_key, output_key, relation, relation_key in [
                ("genres", "genres", "id", "id", "movie_genres", "genre_id"),
                ("production_countries", "countries", "iso_3166_1", "country_code", "movie_countries", "country_code"),
                ("spoken_languages", "languages", "iso_639_1", "language_code", "movie_languages", "language_code"),
                ("keywords", "keywords", "id", "id", "movie_keywords", "keyword_id"),
            ]:
                for item in json_list(source[field], field):
                    key = identifier(item.get(source_key)) if source_key == "id" else text(item.get(source_key))
                    if not key:
                        raise ValueError(f"Missing code in {field}")
                    name = text(item.get("english_name") or item.get("name"))
                    record = {output_key: key, "name": name}
                    remember(table, key, record)
                    tables[relation].append({"movie_id": movie_id, relation_key: key})

            # Original language need not appear in the spoken-language list.
            language = movie["original_language"]
            if language:
                remember("languages", language, {"language_code": language, "name": ""})

            credit = credits.get(movie_id)
            if credit is None:
                missing_credits.append(movie_id)
                continue
            cast = json_list(credit["cast"], "cast")
            for person in cast:
                person["order"] = number(person.get("order"), "cast order", integer=True)
            cast.sort(key=lambda person: int(person["order"]) if person["order"] else float("inf"))
            if cast_limit:
                cast = cast[:cast_limit]
            for person in cast:
                tables["cast"].append({
                    "movie_id": movie_id, "person_id": identifier(person.get("id")),
                    "person_name": text(person.get("name")),
                    "character": text(person.get("character")), "order": person["order"],
                })
            for person in json_list(credit["crew"], "crew"):
                if text(person.get("job")) == "Director":
                    tables["crew"].append({
                        "movie_id": movie_id, "person_id": identifier(person.get("id")),
                        "person_name": text(person.get("name")), "job": "Director",
                    })
        except (ValueError, KeyError) as error:
            raise ValueError(f"Movie {movie_id}: {error}") from error

    for name, records in entities.items():
        tables[name] = list(records.values())
    # Remove only exact repeated rows, retaining source encounter order.
    for name, rows in tables.items():
        fields = TABLE_FIELDS[name]
        tables[name] = list({tuple(row[field] for field in fields): row for row in rows}.values())

    summary = {
        "selected_movies": len(tables["movies"]), "limit": limit, "cast_limit": cast_limit,
        "crew_jobs": ["Director"], "extension": "keywords",
        "movies_without_credits": missing_credits,
        "output_rows": {f"{name}.csv": len(rows) for name, rows in tables.items()},
        "missing_movie_fields": {field: sum(row[field] == "" for row in tables["movies"])
                                 for field in MOVIE_FIELDS},
        "zero_runtime_movies": sum(row["runtime"] == "0" for row in tables["movies"]),
        "zero_vote_movies": sum(row["vote_count"] == "0" for row in tables["movies"]),
    }
    return tables, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=PROJECT_DIR / "data/raw")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_DIR / "data/prepared")
    parser.add_argument("--limit", type=int, default=100, help="First N distinct movies; 0 processes all.")
    parser.add_argument("--cast-limit", type=int, default=10, help="First N actors by credit order; 0 keeps all.")
    args = parser.parse_args()
    if args.limit < 0 or args.cast_limit < 0:
        parser.error("Limits must be nonnegative.")
    movies_path = args.input_dir / "tmdb_5000_movies.csv"
    credits_path = args.input_dir / "tmdb_5000_credits.csv"
    try:
        if args.output_dir.resolve() in {args.input_dir.resolve(), (PROJECT_DIR / "data/ref").resolve()}:
            raise ValueError("Choose an output directory separate from raw and reference data.")
        tables, summary = prepare_tables(movies_path, credits_path, args.limit, args.cast_limit)
        summary["processed_at_utc"] = datetime.now(timezone.utc).isoformat()
        summary["input_files"] = [str(path.resolve()) for path in (movies_path, credits_path)]
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name, rows in tables.items():
            path = args.output_dir / f"{name}.csv"
            with path.open("w", newline="", encoding="utf-8") as output:
                writer = csv.DictWriter(output, fieldnames=TABLE_FIELDS[name])
                writer.writeheader()
                writer.writerows(rows)
            print(f"Created {path.name}: {len(rows)} rows")
        (args.output_dir / "preparation_summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Saved tables and preparation_summary.json in {args.output_dir}")
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
