# Movie Knowledge Graph

A Semantic Web learning project following the architecture of the sibling
`Movie-Knowledge-Graph` reference project.

[video](report/semantic.webm)

# Setup

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


# 1. Define an ontology for the selected domain
![/home/tomodachii/Programming/semantic-web/semantic-web/ontology/ontology.png](file:///home/tomodachii/Programming/semantic-web/semantic-web/ontology/ontology.png)
### Classes
- `kg:Movie` - a movie.
- `kg:Person` - an actor or director.
- `kg:Role` - an acting participation with character and cast-order details.
- `kg:Genre` - a movie genre.
- `kg:Country` - a movie production country.
- `kg:Language` - a language associated with a movie.
- `kg:Keyword` - a movie keyword.
### Object properties
- `kg:actor` - links a movie to a person or role, and a role to a person.
- `kg:countryOfOrigin` - links a movie to a production country.
- `kg:director` - links a movie to its director.
- `kg:genre` - links a movie to a genre.
- `kg:keywords` - links a movie to a keyword.
- `kg:inLanguage` - links a movie to its original or spoken languages.
- `kg:directedMovie` - links a director to a movie; inverse of kg:director.
- `kg:hasCastMember` - links a director to people or roles in movies they directed.
- `kg:referencePage` - links a movie to a reference webpage identifying it.
### Datatype properties
- `kg:abstract` - movie synopsis (xsd:string).
- `kg:characterName` - character name for an acting role (xsd:string).
- `kg:datePublished` - movie release date (xsd:date).
- `kg:duration` - movie runtime (xsd:duration).
- `kg:name` - entity name or movie title (xsd:string).
- `kg:position` - cast order (xsd:integer).
- `kg:ratingValue` - average rating directly on a movie (xsd:decimal).
# 2. Collect relevant data in this domain
We use the TMDB 5000 movie dataset https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata from kaggle
The raw data files are stored in `data/raw/tmdb_5000_movies.csv` and `data/raw/tmdb_5000_credits.csv`.

We prepare the data and split them into csvs file in `data/prepared` 
```
python scripts/prepare.py
```
# 3. Transform collected data into 4* standard
We transform the CSV files in `data/prepared/` into RDF triples using our ontology. Each movie, person, genre, country, language and keyword has its own URI. Dates, ratings and runtimes are stored with their corresponding datatypes.
```
python scripts/transform.py
```
The RDF graph is saved in `output/movies.ttl` in Turtle format. Using RDF and URIs provides the data representation for the 4* standard.
# 4. Find and establish links to other datasets to obtain 5* standard
We link our entities to Wikidata and DBpedia so they can be connected to information in other datasets.
```
python scripts/link_movies.py
python scripts/link_people.py
python scripts/link_lookups.py
```
Movies and people are matched using their TMDB IDs and supporting information. Countries and languages are matched using ISO codes. Approved identity matches use `owl:sameAs`. Genres use `skos:closeMatch` because their meanings may differ between datasets.

The links are saved in:
- `output/movie_links.ttl`
- `output/person_links.ttl`
- `output/lookup_links.ttl`

The scripts also save candidate CSV files with matching evidence and review status. Only approved matches are included in the link files. These external links provide the connections for the 5* standard.
# 5. Provide an interface via SPARQL endpoint/termnal to query data
Using terminal interface to run SPARQL queries against our RDF graph.
```
python scripts/ask.py -q queries/4.sparql
```
Reasoning
```
python scripts/ask.py -q queries/11.sparql --reasoning
python scripts/ask.py -q queries/12.sparql --reasoning
```
The script loads the movie data and ontology, applies reasoning when requested, and prints the query results in the terminal.

To show the external movie links, run:
```
python scripts/ask.py -q queries/show_links.sparql --links output/movie_links.ttl
```
Reasoning runs in memory and does not save an inferred graph file.