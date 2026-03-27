# Atlas data schema

This folder stores lightweight, fillable data files for the globe hover mode and future language analytics.

Primary design goals:
- keep records small and easy to load in the browser
- preserve source traceability for each field
- separate country identity from language records

Suggested sources:
- ISO 3166 for country codes
- ISO 639 for language codes
- UNESCO World Atlas of Languages for multilingual and country-level linguistic references

Files:
- `sources.csv`: source registry
- `countries.csv`: country-level identity and atlas reference
- `country_languages.csv`: per-country language records
- `language_codes.csv`: optional language code lookup table

Notes:
- Leave fields blank when data is unknown.
- Prefer one row per language when a country has multiple official or native languages.
- Add source URLs or citation notes in the source columns.
