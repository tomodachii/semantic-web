"""Check RDF semantics using small prepared CSV fixtures."""

import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from rdflib import Graph, Literal, Namespace, RDF, XSD
from tmdb import TABLE_FIELDS
from transform import SCHEMA, build_graph


class TransformTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.rows = {table: [] for table in TABLE_FIELDS}
        self.rows["movies"] = [{"id": "1", "title": "Film", "original_language": "en",
                                "release_date": "2020-01-02", "runtime": "90", "vote_count": "0"}]
        self.rows["people"] = [{"id": "2", "name": "Person"}]
        self.rows["languages"] = [{"language_code": "en", "name": "English"}]
        self.rows["cast"] = [{"movie_id": "1", "person_id": "2", "person_name": "Person",
                              "character": "Hero", "order": "0", "credit_id": "a"}]
        self.rows["crew"] = [{"movie_id": "1", "person_id": "2", "person_name": "Person",
                              "job": "Director", "department": "Directing", "credit_id": "b"}]
        self.base = Namespace("https://test.example/")
        self.kg = Namespace(str(self.base) + "ontology/")

    def build(self):
        for table, fields in TABLE_FIELDS.items():
            with (self.directory / f"{table}.csv").open("w", newline="", encoding="utf-8") as output:
                writer = csv.DictWriter(output, fieldnames=fields, restval="")
                writer.writeheader()
                writer.writerows(self.rows[table])
        return build_graph(self.directory, str(self.base))

    def test_datatypes_missing_values_and_languages(self):
        graph = self.build()
        movie = self.base["movie/1"]
        self.assertIn((self.base["cast-credit/1-a"], SCHEMA.position, Literal(0, datatype=XSD.integer)), graph)
        self.assertIn((self.base["rating/1"], SCHEMA.ratingCount, Literal(0, datatype=XSD.integer)), graph)
        self.assertIn((movie, SCHEMA.duration, Literal("PT90M", datatype=XSD.duration)), graph)
        self.assertFalse(list(graph.objects(movie, self.kg.revenueUSD)))
        self.assertFalse(list(graph.objects(movie, SCHEMA.inLanguage)))
        self.assertIn((movie, self.kg.originalLanguage, self.base["language/en"]), graph)

    def test_shared_person_and_local_jobs(self):
        graph = self.build()
        person = self.base["person/2"]
        self.assertEqual(list(graph.subjects(RDF.type, SCHEMA.Person)), [person])
        self.assertIn((self.base["cast-credit/1-a"], self.kg.person, person), graph)
        self.assertIn((self.base["crew-credit/1-b"], self.kg.person, person), graph)
        self.assertFalse(list(graph.objects(person, SCHEMA.roleName)))

    def test_missing_reference_is_rejected(self):
        self.rows["cast"][0]["person_id"] = "999"
        with self.assertRaisesRegex(ValueError, "Unknown people"):
            self.build()

    def test_duplicate_and_conflicting_credit(self):
        expected = len(self.build())
        self.rows["cast"].append(dict(self.rows["cast"][0]))
        self.assertEqual(len(self.build()), expected)
        self.rows["cast"][1]["character"] = "Different"
        with self.assertRaisesRegex(ValueError, "conflicting credit"):
            self.build()

    def test_fallback_uri_stability_and_turtle_roundtrip(self):
        self.rows["cast"][0]["credit_id"] = ""
        graph = self.build()
        self.assertEqual(set(graph), set(self.build()))
        decoded = Graph().parse(data=graph.serialize(format="turtle"), format="turtle")
        self.assertEqual(set(graph), set(decoded))


if __name__ == "__main__":
    unittest.main()
