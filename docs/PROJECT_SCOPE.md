# Movie knowledge graph: scope and learning goals

This project describes movies, their cast and directors, genres, production
countries, languages, keywords, and audience ratings. We will keep its first
version close to `Movie-Knowledge-Graph`, but use our own questions and examples.
The EDA, CSV preparation, and local ontology are implemented; RDF generation is implemented in scripts/transform.py.

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
- Movie IDs, titles, overviews, release dates, runtimes,
  original languages, vote averages.
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
| 4.sparql | Which Drama films have the highest average rating? | Genre, rating value | Joins, filtering, ranking |
| 5.sparql | Which films released from 2010 onward feature a selected actor in a selected genre? | Date, actor, genre | Combining graph paths |
| 6.sparql | Which pairs of actors share at least two films in this snapshot? | Movie–person identities | Grouping and counting distinct movies |
| 7.sparql | Which directors have at least two films in this snapshot? | Director–movie relationships | Aggregation and inverse relations |
| 8.sparql | What are each movie's recorded production countries? | Movie–country | Direct movie-origin relationships |
| 9.sparql | Which films have more than one recorded language? | Movie–language relationships | Many-to-many relationships |
| 10.sparql | Which additional facts can Wikidata provide for a linked film? | Verified movie identity links | External linked data |

Thresholds such as 2010 are query choices, not ontology axioms.
Vote counts are omitted, so queries cannot filter by the number of voters.
No query is required to return rows for every possible sample.

## Current model

`kg:` abbreviates our vocabulary, `https://example.org/ontology/`.
The definitions are in `ontology/ontology.owl`; no Schema.org axioms are required.

| Category/class | Particular instances | Information attached to each |
|---|---|---|
| kg:Movie | One film per TMDB movie ID | Title, date, duration, relationships |
| kg:Person | One person per TMDB person ID | Name; shared across acting/directing credits |
| kg:Genre | One genre per genre ID | Genre name; keep kg:genre as the movie relationship |
| kg:Country | One country per country code | Country name |
| kg:Language | One language per language code | Language name |
| kg:Role | One retained acting participation | Actor, character string, cast position |
| kg:Keyword | One keyword per source keyword ID | Label; connect movies using kg:keywords |

Actors and directors are roles played by people. They do not need disjoint
Actor and Director classes. The same person can do both. Genre names such as
Drama will be instances of Genre, not subclasses of Movie.

## What steps 1 and 2 must establish

1. A question has a clear interpretation, required fields, and an example query.
2. The notebook identifies source tables, fields, keys, missingness, and join paths.
3. We can explain why characters belong to an acting role, ratings are decimal literals on movies,
   and shared entities need stable identifiers.
4. We distinguish data checks from OWL inference and avoid inventing facts.
5. We can describe the future CSV layout before implementing its exporter.

Next steps: establish external
links, and expose SPARQL through a terminal or endpoint.
