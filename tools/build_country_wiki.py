import argparse
import csv
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
ATLAS_DIR = ROOT_DIR / "data" / "atlas"
GLOBE_DIR = ROOT_DIR / "static" / "portal" / "globe"
WIKI_DIR = ROOT_DIR / "data" / "wiki"
OUTPUT_PATH = WIKI_DIR / "country_summaries.json"

USER_AGENT = "portal-da-linguagem/1.0 (country summary compiler)"
SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"

TITLE_OVERRIDES = {
    "BHS": "The Bahamas",
    "CPV": "Cape Verde",
    "CIV": "Ivory Coast",
    "COD": "Democratic Republic of the Congo",
    "COG": "Republic of the Congo",
    "CZE": "Czech Republic",
    "GMB": "The Gambia",
    "KOR": "South Korea",
    "LAO": "Laos",
    "MKD": "North Macedonia",
    "PRK": "North Korea",
    "SWZ": "Eswatini",
    "SYR": "Syria",
    "TZA": "Tanzania",
    "USA": "United States",
}


def slugify_title(value: str) -> str:
    collapsed = re.sub(r"\s+", " ", value.strip())
    return collapsed.replace(" ", "_")


def fetch_json(url: str):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def load_country_names():
    country_names = {}
    countries_path = ATLAS_DIR / "countries.csv"
    if countries_path.exists():
        with countries_path.open(newline="", encoding="utf-8") as countries_file:
            for row in csv.DictReader(countries_file):
                iso3 = (row.get("iso3") or "").strip().upper()
                name = (row.get("country_name") or "").strip()
                if iso3 and name:
                    country_names[iso3] = name

    capitals_path = GLOBE_DIR / "capitals.json"
    capitals = json.loads(capitals_path.read_text(encoding="utf-8"))
    for row in capitals:
        iso3 = (row.get("iso_a3") or "").strip().upper()
        if not iso3 or iso3 in country_names:
            continue
        country_names[iso3] = (TITLE_OVERRIDES.get(iso3) or row.get("name") or iso3).strip()

    return country_names


def build_record(iso3: str, country_name: str):
    title = TITLE_OVERRIDES.get(iso3, country_name)
    summary = fetch_json(SUMMARY_URL.format(title=urllib.parse.quote(slugify_title(title), safe="")))
    return {
        "iso3": iso3,
        "country_name": country_name,
        "wiki_title": summary.get("title") or title,
        "summary": summary.get("extract", ""),
        "description": summary.get("description", ""),
        "thumbnail_url": (summary.get("thumbnail") or {}).get("source", ""),
        "wiki_url": ((summary.get("content_urls") or {}).get("desktop") or {}).get("page", ""),
        "source": "Wikipedia",
        "license": "CC BY-SA",
    }


def load_existing():
    if not OUTPUT_PATH.exists():
        return {}
    existing = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    return {row["iso3"]: row for row in existing}


def main():
    parser = argparse.ArgumentParser(description="Fetch and compile country mini-wiki summaries.")
    parser.add_argument("--iso3", nargs="*", help="Optional ISO3 codes to refresh.")
    parser.add_argument("--sleep", type=float, default=0.2, help="Pause between requests.")
    parser.add_argument("--refresh", action="store_true", help="Ignore cached output and rebuild everything.")
    args = parser.parse_args()

    country_names = load_country_names()
    wanted = {code.strip().upper() for code in (args.iso3 or []) if code.strip()}
    existing = {} if args.refresh else load_existing()
    compiled = []

    for iso3 in sorted(country_names):
        if wanted and iso3 not in wanted:
            if iso3 in existing:
                compiled.append(existing[iso3])
            continue

        country_name = country_names[iso3]
        try:
            record = build_record(iso3, country_name)
            compiled.append(record)
            print(f"Fetched {iso3} - {record['wiki_title']}")
        except urllib.error.HTTPError as error:
            print(f"Failed {iso3} ({country_name}): HTTP {error.code}")
            if iso3 in existing:
                compiled.append(existing[iso3])
        except urllib.error.URLError as error:
            print(f"Failed {iso3} ({country_name}): {error.reason}")
            if iso3 in existing:
                compiled.append(existing[iso3])
        time.sleep(args.sleep)

    if not wanted:
        missing = sorted(set(existing) - {row["iso3"] for row in compiled})
        for iso3 in missing:
            compiled.append(existing[iso3])

    compiled.sort(key=lambda row: row["country_name"])
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(compiled, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(compiled)} summaries to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
