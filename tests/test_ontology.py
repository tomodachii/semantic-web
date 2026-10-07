"""Check the ontology's intended inference on a tiny movie graph."""
import unittest
from pathlib import Path

from rdflib import Graph, Namespace, RDF, RDFS, OWL
from owlrl import DeductiveClosure, OWLRL_Semantics

SCHEMA = Namespace("https://schema.org/")
KG = Namespace("https://example.org/ontology/")
EX = Namespace("https://example.org/test/")
ONTOLOGY = Path(__file__).resolve().parents[1] / "ontology/ontology.owl"


class OntologyTests(unittest.TestCase):
    def test_scope_and_restrictions(self):
        g = Graph().parse(ONTOLOGY, format="turtle")
        for term in [SCHEMA.Organization, SCHEMA.productionCompany, SCHEMA.location,
                     KG.imdbPage, KG.productionCountry, SCHEMA.identifier,
                     SCHEMA.CreativeWork, SCHEMA.Thing, SCHEMA.Intangible, SCHEMA.Rating]:
            self.assertFalse(any(term in triple for triple in g), term)
        self.assertIn((SCHEMA.keywords, RDFS.range, SCHEMA.DefinedTerm), g)
        self.assertIn((SCHEMA.genre, RDFS.range, KG.Genre), g)
        self.assertTrue(any(g.objects(SCHEMA.Role, RDFS.subClassOf)))

    def test_inverse_chain_and_keyword_typing_without_role_confusion(self):
        g = Graph().parse(ONTOLOGY, format="turtle")
        g.parse(data='''
            @prefix s: <https://schema.org/> .
            @prefix e: <https://example.org/test/> .
            e:film a s:Movie ; s:name "Film" ; s:director e:director ;
                s:actor e:person, e:role ; s:keywords e:keyword .
            e:director a s:Person ; s:name "Director" .
            e:person a s:Person ; s:name "Actor" .
            e:role a s:Role ; s:actor e:person ;
                s:characterName "Character" ; s:position 0 .
            e:keyword s:name "space" .
        ''', format="turtle")
        self.assertNotIn((EX.director, KG.hasCastMember, EX.person), g)
        DeductiveClosure(OWLRL_Semantics).expand(g)
        self.assertIn((EX.director, KG.directedMovie, EX.film), g)
        self.assertIn((EX.director, KG.hasCastMember, EX.person), g)
        self.assertIn((EX.director, KG.hasCastMember, EX.role), g)
        self.assertIn((EX.keyword, RDF.type, SCHEMA.DefinedTerm), g)
        self.assertNotIn((EX.role, RDF.type, SCHEMA.Person), g)
        self.assertNotIn((EX.role, RDF.type, SCHEMA.Movie), g)
        for left, right in g.subject_objects(OWL.disjointWith):
            self.assertFalse(set(g.subjects(RDF.type, left)) & set(g.subjects(RDF.type, right)))


if __name__ == "__main__":
    unittest.main()
