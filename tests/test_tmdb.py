"""Test preparation with synthetic inputs; the downloaded dataset is not required."""

import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "tmdb.py"
spec = importlib.util.spec_from_file_location("tmdb", SCRIPT)
tmdb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tmdb)


def movie(movie_id):
    row = {field: "" for field in tmdb.MOVIE_FIELDS}
    row.update(id=movie_id, title=" Same title ", runtime="120.0", budget="0",
               revenue="500", vote_count="0", vote_average="0", original_language="en",
               release_date="2000-01-01")
    row.update(genres=json.dumps([{"id": 28, "name": "Action"}] * 2),
               production_companies=json.dumps([{"id": 5, "name": "Studio"}]),
               production_countries=json.dumps([{"iso_3166_1": "US", "name": "United States"}]),
               spoken_languages="[]")
    return row


def credit(movie_id):
    cast = [
        {"id": 20, "name": "Second", "order": 1, "character": "B", "credit_id": "cast-b"},
        {"id": 10, "name": " First ", "order": 0, "character": "A", "credit_id": "cast-a"},
    ]
    crew = [
        {"id": 10, "name": "First", "job": "Director", "department": "Directing"},
        {"id": 10, "name": "First", "job": "Writer", "department": "Writing"},
        {"id": 30, "name": "Other", "job": "Editor", "department": "Editing"},
    ]
    return {"movie_id": movie_id, "cast": json.dumps(cast), "crew": json.dumps(crew)}


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.movies = Path(self.temp.name) / "movies.csv"
        self.credits = Path(self.temp.name) / "credits.csv"

    def prepare(self, movies, credits, **options):
        write_csv(self.movies, movies)
        write_csv(self.credits, credits)
        return tmdb.prepare_tables(self.movies, self.credits, **options)

    def test_join_by_id_cleaning_and_relationships(self):
        tables, summary = self.prepare([movie("1"), movie("2")], [credit("2"), credit("1")],
                                       limit=0, cast_limit=1)
        self.assertEqual(len(tables), 12)
        self.assertEqual([r["id"] for r in tables["movies"]], ["1", "2"])
        self.assertEqual(tables["movies"][0]["title"], "Same title")
        self.assertEqual(tables["movies"][0]["runtime"], "120")
        self.assertEqual(tables["movies"][0]["budget"], "")
        self.assertEqual(tables["movies"][0]["vote_count"], "0")
        self.assertEqual(tables["movies"][0]["vote_average"], "")
        self.assertEqual(len(tables["movie_genres"]), 2)
        self.assertEqual([r["person_id"] for r in tables["cast"]], ["10", "10"])
        self.assertEqual(tables["cast"][0]["order"], "0")
        self.assertEqual({r["job"] for r in tables["crew"]}, {"Director", "Writer"})
        self.assertEqual(tables["people"], [{"id": "10", "name": "First"}])
        self.assertEqual(tables["languages"], [{"language_code": "en", "name": ""}])
        self.assertEqual(summary["output_rows"]["movies.csv"], 2)

    def test_source_limit_full_cast_and_missing_credits(self):
        tables, _ = self.prepare([movie("1"), movie("2")], [credit("1")], limit=1, cast_limit=0)
        self.assertEqual(len(tables["movies"]), 1)
        self.assertEqual(len(tables["cast"]), 2)
        tables, summary = self.prepare([movie("1"), movie("2")], [credit("1")], limit=0)
        self.assertEqual(len(tables["movies"]), 2)
        self.assertEqual(summary["cleaning_counts"]["movies_without_credits"], 1)

    def test_duplicate_ids_and_conflicts(self):
        tables, summary = self.prepare([movie("1"), movie("1")], [credit("1")])
        self.assertEqual(len(tables["movies"]), 1)
        self.assertEqual(summary["cleaning_counts"]["duplicate_movies_rows"], 1)
        changed = movie("1")
        changed["title"] = "Different"
        with self.assertRaisesRegex(ValueError, "Conflicting duplicate"):
            self.prepare([movie("1"), changed], [credit("1")])

    def test_invalid_values_include_movie_context(self):
        for field, value in [("genres", "not JSON"), ("release_date", "2000-02-30"),
                             ("runtime", "NaN"), ("budget", "-1"), ("vote_average", "11")]:
            with self.subTest(field=field):
                row = movie("1")
                row[field] = value
                with self.assertRaisesRegex(ValueError, "Movie 1"):
                    self.prepare([row], [credit("1")])

    def test_required_headers(self):
        with self.assertRaisesRegex(ValueError, "missing columns"):
            self.prepare([{"id": "1", "title": "Film"}], [credit("1")])

    def test_cli_writes_csvs_and_provenance(self):
        input_dir = Path(self.temp.name)
        output_dir = input_dir / "output"
        write_csv(input_dir / "tmdb_5000_movies.csv", [movie("1")])
        write_csv(input_dir / "tmdb_5000_credits.csv", [credit("1")])
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--input-dir", str(input_dir),
             "--output-dir", str(output_dir)],
            cwd=input_dir, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(list(output_dir.glob("*.csv"))), 12)
        summary = json.loads((output_dir / "preparation_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["selected_movies"], 1)
        self.assertEqual(len(summary["input_files"][0]["sha256"]), 64)
        rows = tmdb.read_csv(output_dir / "movies.csv", tmdb.MOVIE_FIELDS)
        self.assertEqual(rows[0]["id"], "1")


if __name__ == "__main__":
    unittest.main()
