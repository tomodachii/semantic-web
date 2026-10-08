"""Save an OWL-RL graph for Fuseki using the reference ask.py reasoning flow."""
import argparse
import time
from pathlib import Path

from rdflib import BNode, URIRef

from ask import PROJECT, load_graph


def remove_non_rdf_triples(graph):
    """Remove generalized inference triples that standard RDF cannot serialize."""
    invalid = [triple for triple in graph
               if not isinstance(triple[0], (URIRef, BNode))
               or not isinstance(triple[1], URIRef)]
    for triple in invalid:
        graph.remove(triple)
    return len(invalid)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rdf", type=Path, default=PROJECT / "output/movies.ttl")
    parser.add_argument("--ontology", type=Path, default=PROJECT / "ontology/ontology.owl")
    parser.add_argument("--links", type=Path, action="append",
                        help="Repeat to load several link files; defaults to output/movie_links.ttl")
    parser.add_argument("--output", type=Path, default=PROJECT / "output/movies_inferred.ttl")
    args = parser.parse_args()
    start = time.perf_counter()
    links = args.links if args.links is not None else [PROJECT / "output/movie_links.ttl"]
    graph = load_graph(args.rdf, args.ontology, links, reasoning=True)
    removed = remove_non_rdf_triples(graph)
    print(f"[graph] Removed {removed} non-RDF triples for Fuseki compatibility")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=args.output, format="turtle")
    print(f"[graph] Saved {len(graph)} triples to {args.output}")
    print(f"[timing] Total: {time.perf_counter() - start:.3f}s")


if __name__ == "__main__":
    main()
