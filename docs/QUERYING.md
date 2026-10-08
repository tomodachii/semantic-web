# Querying and checking our graph

Run commands from semantic-web in your Python environment with requirements.txt installed.

## Ordinary queries

```powershell
python scripts/ask.py -q queries/4.sparql
```

Lists the highest-rated Drama movies. Queries 1-9 use local facts.

## Reasoning

```powershell
python scripts/ask.py -q queries/11.sparql
python scripts/ask.py -q queries/11.sparql --reasoning
python scripts/ask.py -q queries/12.sparql --reasoning
```

Query 11 uses kg:directedMovie: without reasoning the current generated graph
returns zero rows; with reasoning it returns directors and their movies.
Query 12 uses kg:hasCastMember, inferred through directedMovie followed by actor.
It filters for kg:Person to exclude acting-role nodes.

Like the reference, ask.py combines movie facts and ontology axioms in one
RDFLib graph in memory. --reasoning adds inferred triples before querying.
It does not modify the input files, save inferred data, or use Fuseki.
Each invocation loads and reasons again, so reasoning can take time.

## Save the inferred graph for Fuseki

Run from the project directory:

```bash
python scripts/infer.py
```

This loads output/movies.ttl, ontology/ontology.owl, and output/movie_links.ttl,
just like the reference project's ask.py with --reasoning. It uses the same
`DeductiveClosure(OWLRL_Semantics).expand(graph)` call with default settings,
then saves the whole expanded graph as output/movies_inferred.ttl. Original
facts, ontology axioms, links, and valid RDF inferred triples are retained.
After reasoning, the export removes triples with literal subjects or non-IRI
predicates, which are not valid standard RDF and are rejected by Fuseki.
The reference reasoning call and its settings remain unchanged.
The reference ask.py itself does not save
the graph, so serialization is the added export step.

To include all three link files, run:

```bash
python scripts/infer.py --links output/movie_links.ttl --links output/person_links.ttl --links output/lookup_links.ttl
```

In Fuseki, create or select a dataset and upload output/movies_inferred.ttl.
Paste a query from queries/ into its query interface and run it. Queries 11
and 12 can use the saved inferred relationships without additional reasoning.
For a fresh replacement, clear the old dataset data before uploading; uploading
alone adds triples. Regenerate and replace the graph after changing the data,
ontology, or links.

The defaults locate output/movies.ttl and ontology/ontology.owl relative to the
script's project directory. Explicit file arguments and -q are relative to your
current directory. You can override --rdf and --ontology. Once links exist:

```powershell
python scripts/ask.py -q queries/4.sparql --links output/movie_links.ttl
```

The option can be repeated to load the movie, person, and lookup links together:

```powershell
python scripts/ask.py -q queries/4.sparql --links output/movie_links.ttl --links output/person_links.ttl --links output/lookup_links.ttl
```

Links are optional and are loaded only when --links is supplied. This version
implements the reference's local query flow; it does not implement its remote
--target rewriting. Query 10 requires verified external links and network access
and is not part of the local demonstration.

## Checking correctness

```powershell
python scripts/ask.py -q queries/check_missing_names.sparql
python scripts/ask.py -q queries/check_disjoint_types.sparql --reasoning
python -m unittest discover -s tests -v
```

The first query should return zero rows: every movie has a recorded name.
The second should return zero rows: no entity has both of the checked disjoint
types. Run notebooks/03_test_ontology.ipynb for small positive and deliberately
incorrect examples with explanations.

Successful queries do not prove an ontology correct. These tests check specific
behaviors, not full OWL consistency. Under open-world semantics, a missing name
is not automatically a contradiction of the minimum-name restriction. An empty
conflict query means no conflict of that particular form was found.

SELECT results print as a table, ASK as true/false, and CONSTRUCT/DESCRIBE as Turtle.
