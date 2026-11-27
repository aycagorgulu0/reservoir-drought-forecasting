"""Step 20 (integration): catchment areas over which rainfall is averaged.

Input : HydroBASINS v1c, Europe, level 8 (downloaded to data/raw/hydrobasins/ if missing)
Output: data/processed/catchments.csv      one row per catchment
        data/interim/catchments.geojson    polygons, used by step 21
        figures/fig_d2_catchments.png      map for the report

HydroBASINS splits the land into sub-basins (level 8: a few hundred km2 each) and links
each one to the next sub-basin downstream (NEXT_DOWN). A catchment is built by starting
from the sub-basin that contains a point and collecting everything upstream of it.

  headwater  upstream of each key reservoir (point inside the reservoir, from Wikipedia)
  basin      Tajo: upstream of Alcántara dam; Guadiana: upstream of Badajoz; Duero:
             upstream of Saucelle dam (the Spanish parts, before the rivers reach Portugal)
             Júcar: the Júcar district is several rivers draining to the sea, so it is the
             union of the whole river basins of the Júcar, Turia, Mijares, Palancia, Serpis,
             Cenia and the Alicante coastal rivers with reservoirs in our data
"""
import json
import urllib.request
import zipfile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shapefile  # pyshp
from matplotlib.path import Path as MplPath

from paths import CATCHMENT_SHAPES, CATCHMENTS_CSV, FIGURES, HYDROBASINS_DIR

URL = "https://data.hydrosheds.org/file/HydroBASINS/standard/hybas_eu_lev08_v1c.zip"
SHP = HYDROBASINS_DIR / "hybas_eu_lev08_v1c.shp"
BOX = (-10.0, 35.5, 4.5, 44.5)  # lon_min, lat_min, lon_max, lat_max (Iberia)

# (lat, lon)
HEADWATERS = {
    "entrepenas": ("Entrepeñas headwater", "Tajo", "Entrepeñas", (40.5197, -2.7308)),
    "buendia": ("Buendía headwater", "Tajo", "Buendía", (40.4000, -2.7822)),
    "alarcon": ("Alarcón headwater", "Júcar", "Alarcón", (39.6289, -2.2005)),
    "contreras": ("Contreras headwater", "Júcar", "Contreras", (39.5440, -1.5040)),
}
BASIN_OUTLETS = {
    "tajo": ("Tajo (Spanish part)", "Tajo", (39.7258, -6.8825)),          # Alcántara dam
    "guadiana": ("Guadiana (Spanish part)", "Guadiana", (38.8850, -6.9800)),  # Badajoz
    "duero": ("Duero (Spanish part)", "Duero", (41.0425, -6.8053)),        # Saucelle dam
}
JUCAR_RIVERS = {  # one point per river; the whole river basin (MAIN_BAS) is taken
    "Júcar": (39.6289, -2.2005), "Turia": (39.7100, -1.1000), "Mijares": (40.0900, -0.6000),
    "Palancia": (39.8900, -0.5500), "Serpis": (38.8200, -0.3800), "Guadalest": (38.6700, -0.2100),
    "Amadorio": (38.5500, -0.2700), "Cenia": (40.6500, 0.2200),
}

# 1. Load HydroBASINS (download once)
if not SHP.exists():
    HYDROBASINS_DIR.mkdir(parents=True, exist_ok=True)
    zpath = HYDROBASINS_DIR / "hybas_eu_lev08_v1c.zip"
    print("Downloading HydroBASINS level 8 (33 MB) ...")
    urllib.request.urlretrieve(URL, zpath)
    zipfile.ZipFile(zpath).extractall(HYDROBASINS_DIR)

reader = shapefile.Reader(str(SHP))
fields = [f[0] for f in reader.fields[1:]]
recs, shapes = [], {}
for sr in reader.iterShapeRecords():
    x0, y0, x1, y1 = sr.shape.bbox
    if x1 < BOX[0] or x0 > BOX[2] or y1 < BOX[1] or y0 > BOX[3]:
        continue
    rec = dict(zip(fields, sr.record))
    recs.append(rec)
    pts, parts = sr.shape.points, list(sr.shape.parts) + [len(sr.shape.points)]
    shapes[rec["HYBAS_ID"]] = [np.array(pts[a:b]) for a, b in zip(parts[:-1], parts[1:])]
hb = pd.DataFrame(recs).set_index("HYBAS_ID")
print(f"HydroBASINS sub-basins in the Iberian box: {len(hb):,}")

upstream_of = hb.groupby("NEXT_DOWN").groups  # downstream id -> ids flowing into it


def basin_at(lat, lon):
    for hid, rings in shapes.items():
        if any(MplPath(r).contains_point((lon, lat)) for r in rings):
            return hid
    raise ValueError(f"No sub-basin contains ({lat}, {lon})")


def upstream(hid):
    out, todo = set(), [hid]
    while todo:
        h = todo.pop()
        out.add(h)
        todo += [u for u in upstream_of.get(h, []) if u not in out]
    return out


# 2. Build catchments
catch = []
for cid, (name, basin, res, (lat, lon)) in HEADWATERS.items():
    hid = basin_at(lat, lon)
    catch.append({"catchment_id": cid, "name": name, "type": "headwater", "basin": basin,
                  "reservoirs": res, "members": upstream(hid), "check_up_area": hb.at[hid, "UP_AREA"]})
for cid, (name, basin, (lat, lon)) in BASIN_OUTLETS.items():
    hid = basin_at(lat, lon)
    catch.append({"catchment_id": cid, "name": name, "type": "basin", "basin": basin, "reservoirs": "",
                  "members": upstream(hid), "check_up_area": hb.at[hid, "UP_AREA"]})
jucar = set()
for river, (lat, lon) in JUCAR_RIVERS.items():
    main = hb.at[basin_at(lat, lon), "MAIN_BAS"]
    jucar |= set(hb.index[hb["MAIN_BAS"] == main])
catch.append({"catchment_id": "jucar", "name": "Júcar district (8 river basins)", "type": "basin",
              "basin": "Júcar", "reservoirs": "", "members": jucar, "check_up_area": np.nan})

for c in catch:
    c["area_km2"] = round(float(hb.loc[list(c["members"]), "SUB_AREA"].sum()))
    c["subbasins"] = len(c["members"])

order = ["tajo", "guadiana", "jucar", "duero", "entrepenas", "buendia", "alarcon", "contreras"]
table = pd.DataFrame(catch).set_index("catchment_id").loc[order].reset_index()
table[["catchment_id", "name", "type", "basin", "reservoirs", "area_km2"]].to_csv(CATCHMENTS_CSV, index=False)
print(table[["catchment_id", "type", "area_km2", "subbasins", "check_up_area"]].to_string(index=False))

# 3. Polygons for step 21 (GeoJSON, one MultiPolygon per catchment, rings as lon/lat)
features = []
for c in table.itertuples():
    polys = [[r.tolist()] for h in c.members for r in shapes[h]]
    features.append({"type": "Feature", "properties": {"catchment_id": c.catchment_id, "name": c.name},
                     "geometry": {"type": "MultiPolygon", "coordinates": polys}})
CATCHMENT_SHAPES.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
print(f"Saved {CATCHMENTS_CSV.name} and {CATCHMENT_SHAPES.name}")

# 4. Map
colors = {"tajo": "#9ecae1", "guadiana": "#c7e9c0", "jucar": "#fdd0a2", "duero": "#d9d9d9",
          "entrepenas": "#2171b5", "buendia": "#6baed6", "alarcon": "#d94801", "contreras": "#fd8d3c"}
fig, ax = plt.subplots(figsize=(7, 5.2))
for c in table.itertuples():
    for h in c.members:
        for r in shapes[h]:
            ax.fill(r[:, 0], r[:, 1], color=colors[c.catchment_id], lw=0)
for c in table.itertuples():
    if c.type == "basin":
        ax.text(*{"tajo": (-5.2, 40.0), "guadiana": (-5.0, 38.9), "jucar": (-1.4, 39.1),
                  "duero": (-4.6, 41.8)}[c.catchment_id], c.basin, fontsize=10, ha="center")
for cid, (name, basin, res, (lat, lon)) in HEADWATERS.items():
    ax.plot(lon, lat, "k^", ms=6)
    ax.annotate(res, (lon, lat), xytext=(4, 4), textcoords="offset points", fontsize=8)
ax.set_xlim(-9.5, 1.0)
ax.set_ylim(37.0, 43.5)
ax.set_aspect(1 / np.cos(np.radians(40)))
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_title("Rainfall catchments: basins (light) and key-reservoir headwaters (dark)", fontsize=10)
fig.savefig(FIGURES / "fig_d2_catchments.png", dpi=200, bbox_inches="tight")
print("Saved fig_d2_catchments.png")
