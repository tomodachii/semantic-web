import sys
import unittest
from pathlib import Path

from rdflib import URIRef
from rdflib.namespace import OWL, SKOS

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from link_lookups import candidate_rows, genre_variants, link_graph, merge_candidates

LOCAL = {"local_uri": "https://example.org/genre/28", "key": "28", "name": "Action"}


def candidate(item="http://www.wikidata.org/entity/Q1", enwiki="Action film"):
    return {"item": item, "label": "action film", "enwiki": enwiki}


class LookupTests(unittest.TestCase):
    def test_genre_variants(self):
        self.assertEqual(genre_variants("Action"), ["Action film", "action film"])
        self.assertIn("animated film", genre_variants("Animation"))

    def test_merge_groups_by_key_and_item(self):
        rows = [
            {"code": "US", "item": "Q30", "label": "United States", "enwiki": "United States"},
            {"code": "US", "item": "Q30", "label": "United States", "enwiki": "United States"},
            {"code": "GB", "item": "Q145", "label": "United Kingdom"},
        ]
        merged = merge_candidates(rows, "code")
        self.assertEqual(len(merged["US"]), 1)
        self.assertEqual(merged["GB"][0]["enwiki"], "")

    def test_unique_candidate_is_approved(self):
        rows = candidate_rows("genre", LOCAL, [candidate()])
        self.assertEqual((rows[0]["status"], rows[0]["dbpedia_uri"]),
                         ("approved", "http://dbpedia.org/resource/Action_film"))

    def test_several_candidates_need_review(self):
        rows = candidate_rows("country", LOCAL, [candidate(), candidate(item="http://www.wikidata.org/entity/Q2")])
        self.assertEqual({row["status"] for row in rows}, {"review"})
        self.assertEqual(len(link_graph(rows)), 0)

    def test_no_candidate(self):
        self.assertEqual(candidate_rows("genre", LOCAL, [])[0]["status"], "not_found")

    def test_relation_depends_on_class(self):
        genre = link_graph(candidate_rows("genre", LOCAL, [candidate()]))
        country = link_graph(candidate_rows("country", {**LOCAL, "local_uri": "https://example.org/country/US"}, [candidate()]))
        self.assertEqual({p for _, p, _ in genre}, {SKOS.closeMatch})
        self.assertEqual({p for _, p, _ in country}, {OWL.sameAs})
        self.assertIn((URIRef(LOCAL["local_uri"]), SKOS.closeMatch, URIRef("http://www.wikidata.org/entity/Q1")), genre)


if __name__ == "__main__":
    unittest.main()
