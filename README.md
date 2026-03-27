# Portal da Linguagem

Current active application surface:
- `config`: Django project configuration.
- `apps/core`: shared utilities and validators.
- `apps/portal`: public-facing website entry point.
- `templates/portal` and `static/css`: current site presentation.

Archived prototype material lives under `legado`.
It includes earlier domain-model experiments and incomplete operational apps that are not part of the running site right now.

Environment setup:
1. `cd C:\dev\portal_da_linguagem`
2. `python -m venv .venv`
3. `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`
4. `.\.venv\Scripts\python.exe .\manage.py runserver`

Recommended next build steps:
1. Replace placeholder homepage copy with your real biography, services, and contact flow.
2. Add a dedicated commission brief form for clients.
3. Create the first data-storytelling section from your translation/interpreting production data.

Data atlas files live in `data/atlas/` and are intentionally lightweight so the globe can load them without extra overhead.

Mini wiki cache:
1. `.\.venv\Scripts\python.exe .\tools\build_country_wiki.py`
2. This writes `data/wiki/country_summaries.json` from Wikipedia summaries for the current globe country set.
3. Display returned text with attribution and a source link.
