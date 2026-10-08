"""Query local RDF with RDFLib, following the reference ask.py flow."""
import argparse
import time
from pathlib import Path

from owlrl import DeductiveClosure, OWLRL_Semantics
from rdflib import Graph

PROJECT = Path(__file__).resolve().parents[1]


def load_graph(rdf, ontology, links=None, reasoning=False):
    """Load the data and ontology; links is one Turtle path or a list of them."""
    graph = Graph()
    graph.parse(rdf, format="turtle")
    graph.parse(ontology, format="turtle")
    if links is not None:
        for link_file in [links] if isinstance(links, (str, Path)) else links:
            graph.parse(link_file, format="turtle")
    if reasoning:
        DeductiveClosure(OWLRL_Semantics).expand(graph)
    return graph


def print_rdflib_results(results):
    if results.type == "ASK":
        print(str(results.askAnswer).lower())
    elif results.type in {"CONSTRUCT", "DESCRIBE"}:
        print(results.graph.serialize(format="turtle"), end="")
    else:
        headers = [str(v) for v in results.vars]
        rows = [["" if v is None else str(v) for v in row] for row in results]
        widths = [max(len(headers[i]), *(len(row[i]) for row in rows))
                  if rows else len(headers[i]) for i in range(len(headers))]
        print(" | ".join(v.ljust(w) for v, w in zip(headers, widths)))
        print("-+-".join("-" * w for w in widths))
        for row in rows:
            print(" | ".join(v.ljust(w) for v, w in zip(row, widths)))
        print(f"({len(rows)} rows)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rdf", type=Path, default=PROJECT / "output/movies.ttl")
    parser.add_argument("--ontology", type=Path, default=PROJECT / "ontology/ontology.owl")
    parser.add_argument("--links", type=Path, action="append",
                        help="Optional Turtle identity-links file; repeat to load several")
    parser.add_argument("-q", "--query-file", type=Path, required=True)
    parser.add_argument("--reasoning", action="store_true", help="Apply OWL-RL inference in memory")
    args = parser.parse_args()
    start = time.perf_counter()
    query = args.query_file.read_text(encoding="utf-8-sig")
    graph = load_graph(args.rdf, args.ontology, args.links, args.reasoning)
    print(f"[graph] {len(graph)} triples; reasoning {'on' if args.reasoning else 'off'}")
    print_rdflib_results(graph.query(query))
    print(f"[timing] Total: {time.perf_counter() - start:.3f}s")


if __name__ == "__main__":
    main()
