import csv
import json
from pathlib import Path

from django.views.generic import TemplateView


ATLAS_DIR = Path(__file__).resolve().parents[2] / "data" / "atlas"
STATIC_JS_DIR = Path(__file__).resolve().parents[2] / "static" / "js"
STATIC_CSS_DIR = Path(__file__).resolve().parents[2] / "static" / "css"
GLOBE_DATA_DIR = Path(__file__).resolve().parents[2] / "static" / "portal" / "globe"
WIKI_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "wiki"
SOURCE_LABELS = {
    "UNESCO_WAL": "UNESCO WAL",
}


def load_wiki_summaries():
    wiki_path = WIKI_DATA_DIR / "country_summaries.json"
    if not wiki_path.exists():
        return {}

    rows = json.loads(wiki_path.read_text(encoding="utf-8"))
    return {
        (row.get("iso3") or "").strip().upper(): row
        for row in rows
        if (row.get("iso3") or "").strip()
    }


def load_globe_data_points():
    wiki_by_iso3 = load_wiki_summaries()
    countries_by_iso3 = {}
    with (ATLAS_DIR / "countries.csv").open(newline="", encoding="utf-8") as countries_file:
        for row in csv.DictReader(countries_file):
            iso3 = (row.get("iso3") or "").strip().upper()
            if not iso3:
                continue

            countries_by_iso3[iso3] = {
                "country_name": (row.get("country_name") or "").strip(),
                "iso2": (row.get("iso2") or "").strip().upper(),
                "iso3": iso3,
                "lat": None,
                "lng": None,
                "language_name": "",
                "language_role": "",
                "source_label": "",
                "source_url": "",
            }

    with (ATLAS_DIR / "country_languages.csv").open(newline="", encoding="utf-8") as languages_file:
        for row in csv.DictReader(languages_file):
            iso3 = (row.get("iso3") or "").strip().upper()
            point = countries_by_iso3.get(iso3)
            if not point or point["language_name"]:
                continue

            point["language_name"] = (row.get("language_name") or "").strip()
            point["language_role"] = (row.get("language_role") or "").strip()
            source_id = (row.get("source_id") or "").strip()
            point["source_label"] = SOURCE_LABELS.get(source_id, source_id.replace("_", " ").strip())
            point["source_url"] = (row.get("source_url") or "").strip()

    capitals = json.loads((GLOBE_DATA_DIR / "capitals.json").read_text(encoding="utf-8"))
    data_points = []
    seen_iso3 = set()

    for capital in capitals:
        iso3 = (capital.get("iso_a3") or "").strip().upper()
        if not iso3 or iso3 in seen_iso3:
            continue

        atlas_point = countries_by_iso3.get(iso3, {})
        wiki_point = wiki_by_iso3.get(iso3, {})
        data_points.append(
            {
                "country_name": atlas_point.get("country_name") or (capital.get("name") or iso3).strip(),
                "iso2": atlas_point.get("iso2", ""),
                "iso3": iso3,
                "lat": capital["lat"],
                "lng": capital["lon"],
                "language_name": atlas_point.get("language_name", ""),
                "language_role": atlas_point.get("language_role", ""),
                "source_label": atlas_point.get("source_label", ""),
                "source_url": atlas_point.get("source_url", ""),
                "wiki_title": wiki_point.get("wiki_title", ""),
                "wiki_summary": wiki_point.get("summary", ""),
                "wiki_description": wiki_point.get("description", ""),
                "wiki_thumbnail_url": wiki_point.get("thumbnail_url", ""),
                "wiki_url": wiki_point.get("wiki_url", ""),
                "wiki_source": wiki_point.get("source", ""),
                "wiki_license": wiki_point.get("license", ""),
            }
        )
        seen_iso3.add(iso3)

    return sorted(data_points, key=lambda point: point["country_name"])


def get_globe_asset_version():
    globe_bundle = STATIC_JS_DIR / "globe.js"
    return int(globe_bundle.stat().st_mtime) if globe_bundle.exists() else 0


def get_tailwind_asset_version():
    tailwind_bundle = STATIC_CSS_DIR / "tailwind.css"
    return int(tailwind_bundle.stat().st_mtime) if tailwind_bundle.exists() else 0


def get_globe_data_asset_version():
    asset_names = [
        "globe_texture.png",
        "globe_id.png",
        "globe_regions.json",
        "capitals.json",
    ]
    versions = []
    for asset_name in asset_names:
        asset_path = GLOBE_DATA_DIR / asset_name
        if asset_path.exists():
            versions.append(int(asset_path.stat().st_mtime))

    return max(versions, default=0)


class HomeView(TemplateView):
    template_name = "portal/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "service_categories": [
                    {
                        "title": "Serviços Linguisticos e de Comunicação",
                        "description": "Language services for institutional, academic, and technical material.",
                    },
                    {
                        "title": "Interpreting support",
                        "description": "Professional communication support for meetings, events, and multilingual workflows.",
                    },
                    {
                        "title": "Data storytelling",
                        "description": "Visual explorations that connect language work, output history, and measurable impact.",
                    },
                ],
                "highlights": [
                    "Professional profile for linguistics, translation, and interpreting work.",
                    "Client intake path for commissioned language services.",
                    "A portfolio area for data analysis and visualization projects.",
                ],
                "globe_data_points": load_globe_data_points(),
                "globe_asset_version": get_globe_asset_version(),
                "globe_data_asset_version": get_globe_data_asset_version(),
                "tailwind_asset_version": get_tailwind_asset_version(),
            }
        )
        return context
