"""Tests for the reference-style raw CSV splitter (no downloaded data needed)."""
import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/tmdb.py"
spec = importlib.util.spec_from_file_location("tmdb", SCRIPT)
tmdb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tmdb)


def movie(mid):
    row = {field: "" for field in tmdb.MOVIE_FIELDS if field != "imdb_id"}
    row.update(id=mid, title=" Same title ", original_language="en",
               runtime="120.0", vote_average="0", vote_count="0", release_date="2000-01-01")
    row.update({field: "[]" for field in tmdb.NESTED_FIELDS})
    row["genres"] = json.dumps([{"id": 28, "name": "Action"}] * 2)
    row["keywords"] = json.dumps([{"id": 1, "name": "space"}] * 2)
    row["production_companies"] = json.dumps([{"id": 5, "name": "Studio"}])
    return row


def credit(mid):
    return {"movie_id": mid, "cast": json.dumps([
        {"id": 20, "name": "Second", "order": 1, "character": "B"},
        {"id": 10, "name": " First ", "order": 0, "character": "A"},
    ]), "crew": json.dumps([
        {"id": 10, "name": "First", "job": "Director"},
        {"id": 30, "name": "Other", "job": "Writer"},
    ])}


def write(path, rows):
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.movies = self.root / "tmdb_5000_movies.csv"
        self.credits = self.root / "tmdb_5000_credits.csv"

    def prepare(self, movies, credits, **options):
        write(self.movies, movies)
        write(self.credits, credits)
        return tmdb.prepare_tables(self.movies, self.credits, **options)

    def test_id_join_reference_columns_and_keywords(self):
        tables, summary = self.prepare([movie("1"), movie("2")],
                                       [credit("2"), credit("1")], cast_limit=1)
        self.assertEqual(len(tables), 13)
        self.assertEqual(tables["movies"][0]["title"], "Same title")
        self.assertEqual(tables["movies"][0]["runtime"], "120")
        self.assertEqual(tables["movies"][0]["imdb_id"], "")
        self.assertEqual(tables["movies"][0]["vote_average"], "0")
        self.assertEqual(tables["companies"][0]["origin_country"], "")
        self.assertEqual(tables["languages"], [{"language_code": "en", "name": ""}])
        self.assertEqual([r["person_id"] for r in tables["cast"]], ["10", "10"])
        self.assertEqual({r["job"] for r in tables["crew"]}, {"Director"})
        self.assertEqual(len(tables["genres"]), 1)
        self.assertEqual(len(tables["movie_genres"]), 2)
        self.assertEqual(len(tables["keywords"]), 1)
        self.assertEqual(len(tables["movie_keywords"]), 2)
        self.assertEqual(summary["selected_movies"], 2)

    def test_limited_movies_find_reordered_credits(self):
        tables, _ = self.prepare([movie("1"), movie("2")],
                                 [credit("2"), credit("1")], limit=1)
        self.assertEqual({r["movie_id"] for r in tables["cast"]}, {"1"})
        tables, summary = self.prepare([movie("1"), movie("2")], [credit("1")], limit=0)
        self.assertEqual(summary["movies_without_credits"], ["2"])
        self.assertEqual(len(tables["movies"]), 2)

    def test_language_label_fills_placeholder(self):
        second = movie("2")
        second["spoken_languages"] = json.dumps([{"iso_639_1": "en", "name": "English"}])
        tables, _ = self.prepare([movie("1"), second], [credit("1"), credit("2")])
        self.assertEqual(tables["languages"], [{"language_code": "en", "name": "English"}])

    def test_duplicate_and_invalid_source(self):
        changed = movie("1")
        changed["title"] = "Different"
        with self.assertRaisesRegex(ValueError, "Conflicting duplicate"):
            self.prepare([movie("1"), changed], [credit("1")], limit=0)
        for field, value in [("genres", "bad JSON"), ("runtime", "NaN"),
                             ("release_date", "2000-02-30"), ("vote_average", "11")]:
            with self.subTest(field=field):
                row = movie("1")
                row[field] = value
                with self.assertRaisesRegex(ValueError, "Movie 1"):
                    self.prepare([row], [credit("1")])

    def test_cli_writes_exact_tables_and_summary(self):
        write(self.movies, [movie("1")])
        write(self.credits, [credit("1")])
        output = self.root / "prepared"
        result = subprocess.run([sys.executable, str(SCRIPT), "--input-dir", str(self.root),
                                 "--output-dir", str(output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({p.stem for p in output.glob("*.csv")}, set(tmdb.TABLE_FIELDS))
        summary = json.loads((output / "preparation_summary.json").read_text())
        self.assertEqual(summary["output_rows"]["keywords.csv"], 1)


if __name__ == "__main__":
    unittest.main()
