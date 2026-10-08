import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from link_people import (candidate_row, demote_ambiguous, link_graph, linked_films, local_people,
                         merge_candidates, normalize, score_candidate, status_of)

PERSON = {"local_uri": "https://example.org/person/1", "tmdb_person_id": "1", "name": "Zoe Saldana",
          "roles": {"cast"}, "movies": {"19995"}}


def candidate(names=("Zoë Saldaña",), human=True, item="http://www.wikidata.org/entity/Q1"):
    return {"item": item, "label": "Zoë Saldaña", "names": set(names), "imdb": {"nm1"}, "human": human,
            "enwiki": "Zoe Saldaña", "tmdb": {"1"}}


class ScoringTests(unittest.TestCase):
    def test_normalize_ignores_accents_case_punctuation(self):
        self.assertEqual(normalize("Zoë Saldaña"), normalize("zoe saldana"))
        self.assertEqual(normalize("J.K. Simmons"), normalize("J. K. Simmons"))

    def test_identifier_scores(self):
        self.assertEqual(score_candidate(PERSON, candidate(), "identifier"), (1.0, "tmdb_person_id+name"))
        self.assertEqual(score_candidate(PERSON, candidate(names=("Someone Else",)), "identifier")[0], 0.7)
        score, matched_by = score_candidate(PERSON, candidate(human=False), "identifier")
        self.assertEqual((score, status_of(score, matched_by)), (0.0, "rejected"))

    def test_name_fallback_never_auto_approves(self):
        score, matched_by = score_candidate(PERSON, candidate(), "name+filmography")
        self.assertEqual((score, status_of(score, matched_by)), (0.9, "review"))


class RowTests(unittest.TestCase):
    def test_row_and_links(self):
        row = candidate_row(PERSON, candidate(), "identifier")
        self.assertEqual(row["status"], "approved")
        self.assertEqual(row["dbpedia_uri"], "http://dbpedia.org/resource/Zoe_Saldaña")
        self.assertEqual(len(link_graph([row])), 2)

    def test_not_found_row(self):
        self.assertEqual(candidate_row(PERSON, None, "identifier")["status"], "not_found")

    def test_shared_wikidata_item_is_ambiguous(self):
        other = {**PERSON, "local_uri": "https://example.org/person/2", "tmdb_person_id": "2"}
        rows = [candidate_row(PERSON, candidate(), "identifier"), candidate_row(other, candidate(), "identifier")]
        demote_ambiguous(rows)
        self.assertEqual({row["status"] for row in rows}, {"review"})

    def test_two_items_for_one_person_are_ambiguous(self):
        rows = [candidate_row(PERSON, candidate(), "identifier"),
                candidate_row(PERSON, candidate(item="http://www.wikidata.org/entity/Q2"), "identifier")]
        demote_ambiguous(rows)
        self.assertEqual({row["status"] for row in rows}, {"review"})
        self.assertEqual(len(link_graph(rows)), 0)

    def test_merge_candidates(self):
        rows = [
            {"item": "Q1", "label": "A", "alias": "B", "imdb": "nm1", "enwiki": "A", "human": "true", "tmdb": "1"},
            {"item": "Q1", "label": "A", "alias": "C", "imdb": "nm1", "enwiki": "A", "human": "true", "tmdb": "1"},
        ]
        merged = merge_candidates(rows)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["names"], {"A", "B", "C"})
        self.assertTrue(merged[0]["human"])


class InputTests(unittest.TestCase):
    def test_local_people_merges_cast_and_crew(self):
        with tempfile.TemporaryDirectory() as d:
            data = Path(d)
            (data / "cast.csv").write_text("movie_id,person_id,person_name,character,order\n1,7,Ann,X,0\n", encoding="utf-8")
            (data / "crew.csv").write_text("movie_id,person_id,person_name,job\n2,7,Ann,Director\n", encoding="utf-8")
            people = local_people(data, "https://example.org/")
        self.assertEqual(len(people), 1)
        self.assertEqual(people[0]["roles"], {"cast", "director"})
        self.assertEqual(people[0]["movies"], {"1", "2"})
        self.assertEqual(people[0]["local_uri"], "https://example.org/person/7")

    def test_linked_films_reads_wikidata_links_only(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "links.ttl"
            path.write_text(
                "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
                "<https://example.org/movie/1> owl:sameAs <http://www.wikidata.org/entity/Q9>, <http://dbpedia.org/resource/X> .\n",
                encoding="utf-8")
            self.assertEqual(linked_films(path, "https://example.org/"), {"1": {"http://www.wikidata.org/entity/Q9"}})
            self.assertEqual(linked_films(None, "https://example.org/"), {})


if __name__ == "__main__":
    unittest.main()
