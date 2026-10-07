"""Check the ontology's intended inference on a tiny movie graph."""
import unittest
from pathlib import Path

from rdflib import Graph, Namespace, RDF, RDFS, OWL, XSD
from owlrl import DeductiveClosure, OWLRL_Semantics

KG = Namespace("https://example.org/ontology/")
EX = Namespace("https://example.org/test/")
ONTOLOGY = Path(__file__).resolve().parents[1] / "ontology/ontology.owl"


class OntologyTests(unittest.TestCase):
    def test_scope_and_restrictions(self):
        g = Graph().parse(ONTOLOGY, format="turtle")
        self.assertFalse(any(str(term).startswith("https://schema.org/") for triple in g for term in triple))
        for term in [KG.AggregateRating, KG.aggregateRating, KG.ratingCount, KG.Organization, KG.productionCompany, KG.location,
                     KG.imdbPage, KG.productionCountry, KG.identifier,
                     KG.CreativeWork, KG.Thing, KG.Intangible, KG.Rating]:
            self.assertFalse(any(term in triple for triple in g), term)
        self.assertIn((KG.ratingValue, RDFS.domain, KG.Movie), g)
        self.assertIn((KG.ratingValue, RDFS.range, XSD.decimal), g)
        self.assertIn((KG.keywords, RDFS.range, KG.Keyword), g)
        self.assertIn((KG.genre, RDFS.range, KG.Genre), g)
        self.assertTrue(any(g.objects(KG.Role, RDFS.subClassOf)))

    def test_inverse_chain_and_keyword_typing_without_role_confusion(self):
        g = Graph().parse(ONTOLOGY, format="turtle")
        g.parse(data='''
            @prefix kg: <https://example.org/ontology/> .
            @prefix e: <https://example.org/test/> .
            e:film a kg:Movie ; kg:name "Film" ; kg:director e:director ;
                kg:actor e:person, e:role ; kg:keywords e:keyword .
            e:director a kg:Person ; kg:name "Director" .
            e:person a kg:Person ; kg:name "Actor" .
            e:role a kg:Role ; kg:actor e:person ;
                kg:characterName "Character" ; kg:position 0 .
            e:keyword kg:name "space" .
        ''', format="turtle")
        self.assertNotIn((EX.director, KG.hasCastMember, EX.person), g)
        DeductiveClosure(OWLRL_Semantics).expand(g)
        self.assertIn((EX.director, KG.directedMovie, EX.film), g)
        self.assertIn((EX.director, KG.hasCastMember, EX.person), g)
        self.assertIn((EX.director, KG.hasCastMember, EX.role), g)
        self.assertIn((EX.keyword, RDF.type, KG.Keyword), g)
        self.assertNotIn((EX.role, RDF.type, KG.Person), g)
        self.assertNotIn((EX.role, RDF.type, KG.Movie), g)
        for left, right in g.subject_objects(OWL.disjointWith):
            self.assertFalse(set(g.subjects(RDF.type, left)) & set(g.subjects(RDF.type, right)))


if __name__ == "__main__":
    unittest.main()
