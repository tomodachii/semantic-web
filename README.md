# Movie Knowledge Graph

A Semantic Web project using the TMDB 5000 movie dataset.

## Setup

Run from this directory (Python 3.10+):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Download `tmdb_5000_movies.csv` and `tmdb_5000_credits.csv` from
[Kaggle](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata/data) into `data/raw/`.

## Run

```powershell
python scripts/tmdb.py --limit 100 --cast-limit 10
python scripts/transform.py
```

Prepared CSVs go to `data/`; RDF goes to `output/movies.ttl`.
Use `--limit 0 --cast-limit 0` to prepare the full dataset.
To change the development URI prefix:

```powershell
python scripts/transform.py --base-uri https://your-domain.example/
```

Details: [data preparation](docs/DATA_PREPARATION.md),
[RDF mapping](docs/RDF_TRANSFORMATION.md), [project guide](docs/HUONG_DAN_5_SAO.md).
