# Raw TMDB to reference-style CSV tables

Run from semantic-web:

    python scripts/prepare.py

Inputs: data/raw/tmdb_5000_movies.csv and data/raw/tmdb_5000_credits.csv.
Outputs: data/prepared/*.csv and data/prepared/preparation_summary.json.
The script uses only Python's standard library; no API key is required.

By default it selects the first 100 distinct movie IDs in source order, keeps
ten cast entries per movie ordered by source cast position, and keeps all
directors. This is a convenience sample. It is not the reference API's current
popular-movie selection.

    python scripts/prepare.py --limit 0
    python scripts/prepare.py --limit 100 --cast-limit 0

Zero means all movies or all cast members respectively. The credits CSV is
streamed to match selected movie IDs even when the two files are reordered.
Only selected credit rows are retained and their JSON parsed. The program
does not print raw source records.

## What stays close to the reference

The nine retained core files follow the reference layout, with IMDb omitted:

| File | Columns |
|---|---|
| movies.csv | id, title, overview, original_language, release_date, runtime, vote_average |
| genres.csv | id, name |
| movie_genres.csv | movie_id, genre_id |
| countries.csv | country_code, name |
| movie_countries.csv | movie_id, country_code |
| languages.csv | language_code, name |
| movie_languages.csv | movie_id, language_code |
| cast.csv | movie_id, person_id, person_name, character, order |
| crew.csv | movie_id, person_id, person_name, job |

People are described in cast/crew as in the reference; there is no people.csv.
Each nested genre/country/language list becomes a shared entity lookup
and a table of movie–entity pairs. Characters and cast order stay on credit
rows so that the later transformer can create movie-specific Role nodes.

## Our one addition: keywords

- keywords.csv: id, name.
- movie_keywords.csv: movie_id, keyword_id.

This follows the genre-table pattern. The ontology defines kg:Keyword
and links movies using kg:keywords.
It supports a question such as “Which movies share a keyword?” without changing
the core movie, person, and role structure.

## Source differences and cleaning decisions

- IMDb IDs are absent in the raw snapshot and omitted from the output.
- Production companies are excluded from our model and exporter. The raw
  production_companies field is ignored. Movie production countries remain
  in countries.csv and movie_countries.csv and support countryOfOrigin queries.
- Original language is retained separately from the spoken-language table.
  Missing language labels remain empty, but their code gets a lookup row.
- Strip outer whitespace, preserve Unicode, and write UTF-8.
- Validate selected movie dates, nonnegative finite numbers, integer counts,
  source IDs, JSON lists, and scores between 0 and 10.
- Remove exact repeated rows. Reject conflicting duplicate selected IDs or
  nonempty entity labels instead of silently overwriting them.
- Preserve source zeros, like the reference. Runtime 0 needs a documented policy in the RDF stage; the summary counts it.
  Vote counts are not collected.
- Missing credit rows are recorded in the summary and do not discard the movie.
- Omit budget, revenue, additional crew jobs, and other optional extensions.

The existing files directly under data/ are older outputs. Use data/prepared/
as the input to the next ontology/transformation task; data/ref/ is the reference
snapshot and data/raw/ contains original source files. Each run overwrites its
11 named CSVs and summary. Additional unrelated files in a custom output folder
are not part of the manifest in output_rows.

## Verification

    python -m unittest discover -s tests -p test_preparation.py -v

These focused tests check ID-based joins, cast ordering, director selection,
keyword links, missing values, language lookup completion, invalid input, and
CLI output. Older test_tmdb.py and test_transform.py describe the previously
deleted implementation and are not the test contract for this splitter.
