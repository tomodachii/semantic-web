# Movie knowledge graph: scope and learning goals

This project describes movies, their cast and directors, genres, production
countries, languages, keywords, and audience ratings. We will keep its first
version close to `Movie-Knowledge-Graph`, but use our own questions and examples.
The EDA and CSV preparation are implemented; ontology and RDF generation come next.

Notebook 01 reads the reference's 11 CSV tables copied into `../data/ref/`.
Notebook 02 reads a bounded sample (100 rows per file by default) from our raw
TMDB files in `../data/raw/`. It explores how their nested fields can become the
same core table layout, and suggests optional extensions. It does not scan the
full files. Neither notebook reads the older prepared tables directly under data/.
The exporter in scripts/prepare.py writes the agreed layout to data/prepared/;
the raw snapshot and a fresh
popular-movie API collection can contain different movies and available fields.

## Collection boundary

- Approximately 100 movies in a fixed snapshot; a learning sample, not all cinema.
- Up to ten cast members per movie, selected by source credit order.
- All available director credits for those movies. A movie can have multiple directors.
- Movie IDs, IMDb IDs when available, titles, overviews, release dates, runtimes,
  original languages, vote averages, and vote counts.
- Genres, movie production countries, and spoken languages. Production companies are excluded.
- Later: identity links for movies in Wikidata and DBpedia, retaining evidence for review.
- Include keywords as the one small extension: keywords.csv and movie_keywords.csv.
- Defer budget, revenue, producers, writers, recommendations, and a custom website.

An answer means **within this snapshot and its retained credits**. Two actors may
have collaborated outside this sample even when our graph has no such record.
Missing information means unknown; it does not mean the real-world relationship does not exist.

## Competency questions

The matching numbered `.sparql` files live in `../queries/`. They are query
contracts for the planned reference-style graph, not claims that an RDF graph
or endpoint has already been implemented. Their comments explain inputs and assumptions.

| File | Question | Facts needed | Learning goal |
|---|---|---|---|
| 1.sparql | Which films in our snapshot have a known release date, ordered from newest to oldest? | Movie, title, release date | Types, literals, sorting |
| 2.sparql | Which people in the snapshot have both acting and directing credits? | Shared person IDs, actor/director edges | Reusing identities across roles |
| 3.sparql | For a selected film, who are its first ten credited actors and which characters do they play? | Movie, role, person, character, position | Relationship-specific information |
| 4.sparql | Which Drama films have the highest average rating with at least 100 votes? | Genre, rating value, vote count | Joins, filtering, ranking |
| 5.sparql | Which films released from 2010 onward feature a selected actor in a selected genre? | Date, actor, genre | Combining graph paths |
| 6.sparql | Which pairs of actors share at least two films in this snapshot? | Movie–person identities | Grouping and counting distinct movies |
| 7.sparql | Which directors have at least two films in this snapshot? | Director–movie relationships | Aggregation and inverse relations |
| 8.sparql | What are each movie's recorded production countries? | Movie–country | Direct movie-origin relationships |
| 9.sparql | Which films have more than one recorded spoken language? | Movie–language relationships | Many-to-many relationships |
| 10.sparql | Which additional facts can Wikidata provide for a linked film? | Verified movie identity links | External linked data |

Thresholds such as 100 votes and 2010 are query choices, not ontology axioms.
A high average with few votes is not the same evidence as a high average with many votes.
No query is required to return rows for every possible sample.

## Proposed model

`schema:` abbreviates `https://schema.org/`; `kg:` is our own vocabulary.
The actual ontology will be written in a later step.

| Category/class | Particular instances | Information attached to each |
|---|---|---|
| schema:Movie | One film per TMDB movie ID | Title, date, duration, relationships |
| schema:Person | One person per TMDB person ID | Name; shared across acting/directing credits |
| kg:Genre | One genre per genre ID | Genre name; keep schema:genre as the movie relationship |
| schema:Country | One country per country code | Country name |
| schema:Language | One language per language code | Language name |
| schema:Role | One retained acting participation | Actor, character string, cast position |
| schema:AggregateRating | One rating summary per movie in this snapshot | Vote average and count |
| kg:Keyword | One keyword per source keyword ID | Label; connect movies using kg:hasKeyword |

Actors and directors are roles played by people. They do not need disjoint
Actor and Director classes. The same person can do both. Genre names such as
Drama will be instances of Genre, not subclasses of Movie.

## What steps 1 and 2 must establish

1. A question has a clear interpretation, required fields, and an example query.
2. The notebook identifies source tables, fields, keys, missingness, and join paths.
3. We can explain why characters belong to an acting role, ratings form a group,
   and shared entities need stable identifiers.
4. We distinguish data checks from OWL inference and avoid inventing facts.
5. We can describe the future CSV layout before implementing its exporter.

Next steps: write the OWL file, implement CSV-to-RDF mapping from data/prepared/,
test reasoning, establish external
links, and expose SPARQL through a terminal or endpoint.
