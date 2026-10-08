import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from rdflib import Graph
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ask import load_graph, print_rdflib_results

class AskTests(unittest.TestCase):
    def test_optional_links_and_inference(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "data.ttl").write_text('<urn:film> <https://example.org/ontology/director> <urn:person> .')
            ontology = Path(__file__).resolve().parents[1] / "ontology/ontology.owl"
            q = 'ASK { <urn:person> <https://example.org/ontology/directedMovie> <urn:film> }'
            self.assertFalse(load_graph(p / "data.ttl", ontology).query(q).askAnswer)
            self.assertTrue(load_graph(p / "data.ttl", ontology, reasoning=True).query(q).askAnswer)
            (p / "links.ttl").write_text('<urn:film> <http://www.w3.org/2002/07/owl#sameAs> <urn:remote> .')
            g = load_graph(p / "data.ttl", ontology, p / "links.ttl")
            self.assertTrue(g.query('ASK { <urn:film> <http://www.w3.org/2002/07/owl#sameAs> <urn:remote> }').askAnswer)

    def test_several_link_files(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "data.ttl").write_text('<urn:film> <https://example.org/ontology/director> <urn:person> .')
            (p / "movies.ttl").write_text('<urn:film> <http://www.w3.org/2002/07/owl#sameAs> <urn:remote-film> .')
            (p / "people.ttl").write_text('<urn:person> <http://www.w3.org/2002/07/owl#sameAs> <urn:remote-person> .')
            ontology = Path(__file__).resolve().parents[1] / "ontology/ontology.owl"
            g = load_graph(p / "data.ttl", ontology, [p / "movies.ttl", p / "people.ttl"])
            for subject, remote in [("film", "remote-film"), ("person", "remote-person")]:
                q = f'ASK {{ <urn:{subject}> <http://www.w3.org/2002/07/owl#sameAs> <urn:{remote}> }}'
                self.assertTrue(g.query(q).askAnswer)

    def test_result_formats(self):
        g = Graph().parse(data='<urn:a> <urn:p> "value" .', format='turtle')
        for query, expected in [('ASK { ?s ?p ?o }', 'true'),
                                ('SELECT ?o WHERE { ?s ?p ?o }', 'value'),
                                ('CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }', 'value'),
                                ('SELECT ?s WHERE { ?s <urn:missing> ?o }', '(0 rows)')]:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                print_rdflib_results(g.query(query))
            self.assertIn(expected, output.getvalue())
