import json
import hashlib
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from geobr import read_state

#=============================================================================
# CONFIGURAÇÃO DE DIRETÓRIOS E CONSTANTES
#=============================================================================

TOOLS_DIR = Path(__file__).resolve().parent
ROOT_DIR = TOOLS_DIR.parent

OUT_DIR = ROOT_DIR / "static" / "portal" / "globe"
OUT_DIR.mkdir(parents=True, exist_ok=True)

WIDTH, HEIGHT = 4096, 2048
DPI = 300

COUNTRIES_PATH = TOOLS_DIR / "ne_50m_admin_0_countries.json"
CAPITALS_PATH = TOOLS_DIR / "ne_50m_populated_places.json"
# Paletas de cores para as regiões, escolhidas para serem distintas e agradáveis visualmente.
PALETTE = [
    "#2E86AB",
    "#F6AE2D",
    "#F26419",
    "#86BBD8",
    "#2F4858",
    "#9BC53D",
    "#5BC0EB",
    "#E55934",
]

#=============================================================================
#  FUNÇÕES AUXILIARES
#=============================================================================
def stable_color(key: str) -> str:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return PALETTE[int(digest[:8], 16) % len(PALETTE)]


def id_to_rgb(i: int) -> tuple[int, int, int]:
    return (i & 255, (i >> 8) & 255, (i >> 16) & 255)


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#%02X%02X%02X" % rgb


def setup_axes():
    fig = plt.figure(figsize=(WIDTH / DPI, HEIGHT / DPI), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.axis("off")
    return fig, ax


countries = gpd.read_file(COUNTRIES_PATH).to_crs("EPSG:4326")

countries = countries[
    (countries["CONTINENT"].isin(["Africa", "Asia", "South America"]))
    | (
        (countries["CONTINENT"] == "North America")
        & (countries["SUBREGION"].isin(["Central America", "Caribbean"]))
    )
    | (countries["ISO_A3"] == "MEX")
]

countries = countries[countries["ISO_A3"] != "BRA"]

states = read_state(year=2020).to_crs("EPSG:4326")
states["region_id"] = states["abbrev_state"].apply(lambda s: f"BR-{s}")
states["region_name"] = states["name_state"]
states["region_type"] = "br_state"

countries["region_id"] = countries["ISO_A3"]
countries["region_name"] = countries["ADMIN"]
countries["region_type"] = "country"

regions = pd.concat(
    [
        countries[["region_id", "region_name", "region_type", "geometry"]],
        states[["region_id", "region_name", "region_type", "geometry"]],
    ],
    ignore_index=True,
)

regions = gpd.GeoDataFrame(regions, crs="EPSG:4326")

regions["fill_hex"] = regions["region_id"].apply(stable_color)

rgb_map: dict[str, tuple[int, int, int]] = {}
for i, rid in enumerate(regions["region_id"], start=1):
    rgb_map[rid] = id_to_rgb(i)

regions["id_hex"] = regions["region_id"].apply(lambda r: rgb_to_hex(rgb_map[r]))

fig, ax = setup_axes()

regions.translate(-0.4, 0.4).plot(ax=ax, color="white", alpha=0.2)
regions.translate(0.4, -0.4).plot(ax=ax, color="black", alpha=0.22)

regions.plot(ax=ax, color=regions["fill_hex"], edgecolor="#111111", linewidth=0.9)

fig.savefig(OUT_DIR / "globe_texture.png", dpi=DPI, transparent=True)
plt.close(fig)

fig, ax = setup_axes()

regions.plot(
    ax=ax,
    color=regions["id_hex"],
    edgecolor="none",
    linewidth=0,
    antialiased=False,
)

fig.savefig(OUT_DIR / "globe_id.png", dpi=DPI, transparent=True)
plt.close(fig)

regions_json = {}
for rid, rgb in rgb_map.items():
    row = regions[regions["region_id"] == rid].iloc[0]
    regions_json[f"{rgb[0]},{rgb[1]},{rgb[2]}"] = {
        "id": rid,
        "name": row["region_name"],
        "type": row["region_type"],
    }

(OUT_DIR / "globe_regions.json").write_text(
    json.dumps(regions_json, ensure_ascii=False),
    encoding="utf-8",
)

places = gpd.read_file(CAPITALS_PATH).to_crs("EPSG:4326")
capitals = places[places["FEATURECLA"] == "Admin-0 capital"]

keep_iso = set(countries["region_id"]) | {"BRA"}
capitals = capitals[capitals["ADM0_A3"].isin(keep_iso)]

cap_list = [
    {
        "name": r["NAME"],
        "iso_a3": r["ADM0_A3"],
        "lat": r.geometry.y,
        "lon": r.geometry.x,
    }
    for _, r in capitals.iterrows()
]

(OUT_DIR / "capitals.json").write_text(
    json.dumps(cap_list, ensure_ascii=False),
    encoding="utf-8",
)

print(f"Assets gerados com sucesso em: {OUT_DIR}")
