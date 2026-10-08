import sys
import unittest
from pathlib import Path

from rdflib import BNode, Graph, Literal, RDF, URIRef

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from infer import remove_non_rdf_triples


class InferExportTests(unittest.TestCase):
    def test_export_removes_invalid_positions_and_preserves_literal_objects(self):
        graph = Graph()
        movie = URIRef("urn:movie")
        date = Literal("2015-02-13")
        valid = {(movie, URIRef("urn:date"), date),
                 (BNode(), RDF.type, URIRef("urn:Role"))}
        for triple in valid:
            graph.add(triple)
        graph.add((date, RDF.type, URIRef("urn:Date")))
        graph.add((movie, BNode(), date))
        self.assertEqual(remove_non_rdf_triples(graph), 2)
        self.assertEqual(set(graph), valid)
        self.assertEqual(len(Graph().parse(data=graph.serialize(format="turtle"),
                                          format="turtle")), len(valid))
