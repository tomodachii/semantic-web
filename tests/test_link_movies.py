import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import link_movies
from link_movies import dbpedia_uri, link_graph, merge_candidates, movie_rows, score_candidate, status_of, year_of

MOVIE = {"local_uri": "https://example.org/movie/1", "tmdb_id": "1", "title": "Avatar", "release_date": "2009-12-10"}


def candidate(years, item="http://www.wikidata.org/entity/Q1", enwiki="Avatar (2009 film)"):
    return {"item": item, "label": "Avatar", "imdb": {"tt0499549"}, "years": set(years), "enwiki": enwiki}


class ScoringTests(unittest.TestCase):
    def test_identifier_scores(self):
        self.assertEqual(score_candidate(MOVIE, candidate({"2009"}), "identifier"), (1.0, "tmdb_id+release_year"))
        self.assertEqual(score_candidate(MOVIE, candidate({"2010"}), "identifier")[0], 0.7)
        self.assertEqual(score_candidate(MOVIE, candidate({"2013"}), "identifier")[0], 0.0)
        self.assertEqual(score_candidate(MOVIE, candidate(set()), "identifier")[0], 0.5)

    def test_any_wikidata_release_year_can_match(self):
        self.assertEqual(score_candidate(MOVIE, candidate({"2008", "2009"}), "identifier")[0], 1.0)

    def test_title_match_never_auto_approves(self):
        score, matched_by = score_candidate(MOVIE, candidate({"2009"}), "title")
        self.assertEqual((score, status_of(score, matched_by)), (0.9, "review"))

    def test_status(self):
        self.assertEqual(status_of(0.0, "tmdb_id+release_year_mismatch"), "rejected")
        self.assertEqual(status_of(0.7, "tmdb_id+release_year_near"), "review")


class HelperTests(unittest.TestCase):
    def test_year_of(self):
        self.assertEqual(year_of("2009-12-18T00:00:00Z"), "2009")
        self.assertIsNone(year_of(""))
        self.assertIsNone(year_of(None))

    def test_dbpedia_uri(self):
        self.assertEqual(dbpedia_uri("Avatar (2009 film)"), "http://dbpedia.org/resource/Avatar_(2009_film)")
        self.assertEqual(dbpedia_uri("Léa Seydoux"), "http://dbpedia.org/resource/Léa_Seydoux")
        self.assertEqual(dbpedia_uri("AC/DC"), "http://dbpedia.org/resource/AC%2FDC")

    def test_merge_candidates(self):
        rows = [
            {"item": "Q1", "label": "A", "imdb": "tt1", "date": "2009-12-10T00:00:00Z", "enwiki": "A"},
            {"item": "Q1", "label": "A", "imdb": "tt1", "date": "2010-01-01T00:00:00Z", "enwiki": "A"},
        ]
        merged = merge_candidates(rows)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["years"], {"2009", "2010"})


class MovieRowsTests(unittest.TestCase):
    def rows(self, by_id, by_title=()):
        with mock.patch.object(link_movies, "identifier_candidates", return_value=by_id), \
                mock.patch.object(link_movies, "title_candidates", return_value=list(by_title)):
            return movie_rows(MOVIE, session=None)

    def test_identifier_match_is_approved_with_both_links(self):
        rows = self.rows([candidate({"2009"})])
        self.assertEqual(rows[0]["status"], "approved")
        graph = link_graph(rows)
        self.assertEqual(len(graph), 2)

    def test_two_approved_candidates_are_ambiguous(self):
        rows = self.rows([candidate({"2009"}), candidate({"2009"}, item="http://www.wikidata.org/entity/Q2")])
        self.assertEqual({row["status"] for row in rows}, {"review"})
        self.assertEqual(len(link_graph(rows)), 0)

    def test_title_fallback_drops_distant_years(self):
        rows = self.rows([], [candidate({"1999"}), candidate({"2009"}, item="http://www.wikidata.org/entity/Q3")])
        self.assertEqual([row["wikidata_uri"] for row in rows], ["http://www.wikidata.org/entity/Q3"])
        self.assertEqual(rows[0]["status"], "review")

    def test_nothing_found(self):
        self.assertEqual(self.rows([])[0]["status"], "not_found")


if __name__ == "__main__":
    unittest.main()
