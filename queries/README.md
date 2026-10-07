# Competency questions as SPARQL contracts

These are our own variants of the reference project's questions. Read the
question and explanation at the top of each numbered file first.

The queries target the **planned** reference-style RDF model. They do not run
on CSV files, and this stage does not create RDF or `ask.py`.

- Q1–Q9: local queries. Q7 documents an inferred inverse shortcut; Q8 uses
  movie countryOfOrigin directly, with no production companies.
- Q3 and Q5: replace the example `VALUES` URI with an ID from the notebook.
- Q10: federated query intended for a SPARQL engine supporting `SERVICE`, such as
  a suitably configured Fuseki instance. It requires verified local links and
  network access. It is not compatible with the reference CLI's limited remote
  rewriting as-is; that CLI integration is a later task.
- The example namespace `https://example.org/` is a development placeholder.
- `schema:genre` connects to a resource of our proposed `kg:Genre` class.
- Direct `schema:actor` edges connect films to people. Additional actor edges
  connect films to `schema:Role` nodes and those roles to people.
- `schema:inLanguage` is reserved here for spoken languages. The reference
  combines original and spoken language using that predicate; we will need to
  keep original language separate to answer Q9 precisely.

Do not interpret an empty result as a broken query automatically. A fixed sample
may have no matching data. These files will be executed against the generated
graph in the later transformation stage.

Validation for this lesson: all ten files parse as SPARQL. Q1–Q9 were also
smoke-tested against the reference's checked-in `output/movies.ttl`; all returned
results with the included example parameters. That checks compatibility with
the existing graph shape, not the correctness of our future transformer.
In particular, Q9's precise spoken-language meaning still requires the mapping
distinction explained above. Q10 was syntax-checked without contacting Wikidata.
