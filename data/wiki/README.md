# Country wiki cache

This directory stores compiled country summary records for the homepage globe.

Primary file:
- `country_summaries.json`: cached Wikipedia-derived summary records keyed by country `iso3`

Build command:
- `.\.venv\Scripts\python.exe .\tools\build_country_wiki.py`

Notes:
- The compiler reads the current supported country set from `static/portal/globe/capitals.json`.
- Country names from `data/atlas/countries.csv` take precedence when available.
- Wikipedia summaries should be displayed with source attribution and a link back to the article.
