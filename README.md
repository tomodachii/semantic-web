# Movie Knowledge Graph

A Semantic Web learning project following the architecture of the sibling
`Movie-Knowledge-Graph` reference project.

## Start here

1. Read [the scope and competency questions](docs/PROJECT_SCOPE.md).
2. Read the comments in [the numbered SPARQL queries](queries/README.md).
3. Open [01_eda_ref.ipynb](notebooks/01_eda_ref.ipynb) to understand the reference's prepared tables.
4. Open [02_eda_raw.ipynb](notebooks/02_eda_raw.ipynb) to explore our raw TMDB data and plan its model.

Notebook 01 reads the reference's **11 CSV tables** from `data/ref/`.
It explains every field, follows one movie
through the tables, plots relevant distributions, introduces classes and
instances, and shows how nested TMDB responses become the table layout.
It ends with an observation-to-modeling-decision table.

Notebook 02 reads at most 100 rows from each of `tmdb_5000_movies.csv` and
`tmdb_5000_credits.csv` in `data/raw/`. It explains nested JSON, identity joins,
classes and instances, credit roles, constraints, missing source fields, and
optional extensions such as keywords. It demonstrates table splitting in memory.
Its findings describe the bounded sample; it does not scan the full files.

The query files are contracts for the planned RDF model; they will be run
against the graph in a later stage. CSV preparation is now implemented below.

## Setup

Run from this directory (Python 3.10+):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

In your IDE, select the Python environment containing the EDA dependencies as
the notebook kernel. Both notebooks locate this project's data from the workspace
root, project root, or notebooks directory and require no API key or network calls.

The older prepared files directly under `data/` are not used by these lessons.
Notebook 01 uses `data/ref/`; notebook 02 uses the two raw TMDB files in `data/raw/`.

## Prepare our CSV tables

Run from this directory:

```powershell
python scripts/prepare.py
```

This creates 11 tables (nine retained reference tables plus `keywords.csv` and
`movie_keywords.csv`) in `data/prepared/`, using 100 movies, up to ten actors
per movie, and directors only. The script uses the Python standard library.
Use `--limit 0` to process every movie, or `--cast-limit 0` to keep all cast.
Production companies are excluded; movie countries remain available.
IMDb IDs are omitted because the raw files do not supply them.
See [data preparation](docs/DATA_PREPARATION.md) for the
table contract, cleaning decisions, and test command.

## Later steps

Establish external identity links and provide SPARQL access. The scope
document and notebook explain the decisions these steps will implement.

## Test the ontology

Open [03_test_ontology.ipynb](notebooks/03_test_ontology.ipynb) and run all cells
using an environment with the packages in requirements.txt. The notebook uses
small invented examples to show inference, exact SPARQL answers, conflicts,
and the limits of OWL restrictions. Outputs and a reasoning diagram are saved.

The ontology uses our own `kg:` vocabulary (`https://example.org/ontology/`),
including `kg:Keyword`. `kg:referencePage` is an ordinary webpage link;
`owl:sameAs` is reserved for verified identity links. Earlier EDA notebooks and
the hand-drawn ontology.png describe earlier designs; ontology.owl and
CONCEPTS.md are the current vocabulary reference.

## Transform prepared CSVs into RDF

Run from semantic-web with the environment containing rdflib:

```powershell
python scripts/transform.py
```

Reads the 11 tables in data/prepared/ and writes output/movies.ttl.
Optional arguments: --data-dir, --output, --base-uri. Defaults are relative
 to the project directory, so the script also runs from the workspace root.

The script follows the reference transformer: shared ID-based entity URIs,
typed date/duration/numeric literals, direct actor links, and acting-role blank
nodes when character or order is available. Our differences are kg vocabulary,
keywords, director-only crew, a decimal rating directly on each movie, and
kg:referencePage links to TMDB. Empty values are omitted; numeric zeros remain.
Original and spoken languages share kg:inLanguage. No companies or IMDb data
are required. Ontology axioms remain in ontology/ontology.owl; inference and
verified external identity links are separate later steps.

Run checks with `python -m unittest discover -s tests -v`.

## Link movies to Wikidata and DBpedia

```powershell
python scripts/link_movies.py
```

The script reads data/prepared/movies.csv, builds the same movie URIs as
transform.py, and queries the public Wikidata SPARQL endpoint, so network
access is required. Each movie is first matched by its TMDB movie ID (Wikidata
P4947). Movies without an ID match are searched by exact title among Wikidata
films released within one year of the local release date. For every candidate,
the Wikidata release years, the IMDb ID, and the English Wikipedia article are
recorded as evidence. The article title determines the DBpedia resource.

Scoring is conservative. A candidate is approved automatically only when the
TMDB ID matches and a Wikidata release year equals the local year. A one-year
difference, a missing date, a title-only match, or several approved candidates
for one movie result in the status `review`. A difference of more than one year
results in `rejected`.

Outputs:

- output/movie_candidates.csv: every candidate with its evidence, score, and
  status (`approved`, `review`, `rejected`, `not_found`).
- output/movie_links.ttl: `owl:sameAs` triples to Wikidata and DBpedia for
  approved candidates only.

Optional arguments: --data-dir, --base-uri, --candidates, --links, --delay,
--limit (restricts the run to the first N movies).

## Link people to Wikidata and DBpedia

```powershell
python scripts/link_people.py
```

The script links the 825 distinct people in data/prepared/cast.csv and
crew.csv. It must run after link_movies.py because the fallback search uses
output/movie_links.ttl. People are first matched in batches by TMDB person ID
(Wikidata P4985). A candidate is approved automatically only when it is a human
(P31 Q5) and its label or an alias equals the local name, ignoring case,
accents, and punctuation. A person without an ID match is searched by exact
name among the cast (P161) and directors (P57) of the movies linked in
output/movie_links.ttl; such matches always have the status `review`.

Outputs:

- output/person_candidates.csv: every candidate with the person's roles, the
  number of movies, the evidence, and the status. A person with several
  approved candidates, or a Wikidata item claimed by several people, is set to
  `review`.
- output/person_links.ttl: `owl:sameAs` triples for approved candidates only.

Optional arguments: --data-dir, --base-uri, --movie-links, --candidates,
--links, --delay, --limit.

## Link countries, languages and genres

```powershell
python scripts/link_lookups.py
```

The script links the lookup tables in data/prepared/: 19 countries, 23
languages, and 14 genres. Countries are matched by ISO 3166-1 alpha-2 code
(Wikidata P297) and languages by ISO 639-1 code (P218); both are linked with
`owl:sameAs`. Wikidata has no TMDB genre identifier, so genres are matched by
the label of a film genre (Q201658 and its subclasses), such as "action film"
or "animated film". Because a TMDB genre is not defined identically to the
Wikidata genre, genres are linked with the weaker `skos:closeMatch`. For every
class, a single candidate is approved and several candidates are set to
`review`.

Outputs:

- output/lookup_candidates.csv: every candidate with its status.
- output/lookup_links.ttl: link triples for approved candidates only.

Optional arguments: --data-dir, --base-uri, --candidates, --links.

## Query the RDF

Use `python scripts/ask.py -q queries/4.sparql`. Add `--reasoning` for
queries 11 and 12. See [querying and checks](docs/QUERYING.md) for commands
and explanations of what the checks establish.
