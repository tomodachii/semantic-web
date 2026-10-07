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
