"""Step 32 (transformation): build the final modelling table and its data card.

Input : data/interim/features_monthly.csv                    (step 31)
        data/processed/catchments.csv, rainfall_monthly.csv  (steps 20-21, optional)
        data/processed/climate_indices.csv                   (step 22, optional)
Output: data/processed/model_table.csv.gz
        reports/deliverable_2/tables/data_card.csv

Rainfall and climate files are joined only if they exist, so the pipeline runs before
the rainfall branch is merged; rerunning after the merge adds those columns.

Rainfall per reservoir: the 4 key reservoirs use their own headwater catchment, each
combined system the mean of its members' headwaters, every other reservoir its basin.
"""
import unicodedata

import numpy as np
import pandas as pd

from paths import CATCHMENTS_CSV, CLIMATE_CSV, D2_TABLES, FEATURES_CSV, MODEL_TABLE, RAINFALL_CSV
from study_area import KEY_RESERVOIRS, SYSTEMS

PRECIP_WINDOWS = [3, 6, 12, 24, 36]


def ascii_id(name):
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower().replace(" ", "_")


df = pd.read_csv(FEATURES_CSV, parse_dates=["month"])
n = len(df)
df = df[df["pct"].notna()].copy()
print(f"Features: {n:,} rows; dropped {n - len(df)} months with no storage value -> {len(df):,} rows")

# Rainfall (optional)
if RAINFALL_CSV.exists() and CATCHMENTS_CSV.exists():
    rain = pd.read_csv(RAINFALL_CSV, parse_dates=["month"]).sort_values(["catchment_id", "month"])
    for w in PRECIP_WINDOWS:
        rain[f"precip_sum{w}"] = (rain.groupby("catchment_id")["precip_mm"]
                                  .transform(lambda s: s.rolling(w, min_periods=w).sum()))
    rain_cols = [c for c in rain.columns if c not in ("catchment_id", "month")]

    # reservoir -> list of catchments to average
    links = []
    for res, basin in df[["reservoir", "basin"]].drop_duplicates().itertuples(index=False):
        if res in SYSTEMS:
            ids = [ascii_id(r) for r in SYSTEMS[res]["members"]]
        elif res in KEY_RESERVOIRS:
            ids = [ascii_id(res)]
        else:
            ids = [ascii_id(basin)]
        links += [{"reservoir": res, "catchment_id": i} for i in ids]
    links = pd.DataFrame(links)
    known = set(pd.read_csv(CATCHMENTS_CSV)["catchment_id"])
    missing = set(links["catchment_id"]) - known
    if missing:
        print(f"WARNING: catchments not in catchments.csv: {sorted(missing)}")
    per_res = (links.merge(rain, on="catchment_id")
               .groupby(["reservoir", "month"])[rain_cols].mean().reset_index())
    df = df.merge(per_res, on=["reservoir", "month"], how="left")
    print(f"Rainfall joined: {len(rain_cols)} columns, coverage {df['precip_mm'].notna().mean():.1%}")
else:
    rain_cols = []
    print("Rainfall files not found (run steps 20-21 first): table built without rainfall")

# Climate indices (optional)
if CLIMATE_CSV.exists():
    ci = pd.read_csv(CLIMATE_CSV, parse_dates=["month"]).sort_values("month")
    for c in ["nao", "wemo"]:
        for w in [3, 6, 12]:
            ci[f"{c}_mean{w}"] = ci[c].rolling(w, min_periods=w).mean()
    clim_cols = [c for c in ci.columns if c != "month"]
    df = df.merge(ci, on="month", how="left")
    print(f"Climate indices joined: {len(clim_cols)} columns")
else:
    clim_cols = []
    print("Climate index file not found: table built without NAO / WeMO")

df.to_csv(MODEL_TABLE, index=False, float_format="%.4f")
size_mb = MODEL_TABLE.stat().st_size / 1e6
print(f"Saved {MODEL_TABLE.name}: {len(df):,} rows x {df.shape[1]} columns ({size_mb:.1f} MB)")
print(df.groupby("split").agg(rows=("month", "size"), first=("month", "min"), last=("month", "max")).to_string())

# Data card: one row per column
def describe(col):
    if col in ("basin", "role", "reservoir", "is_system"):
        return "identifier", "BD-Embalses", ""
    if col in ("month", "year", "month_num", "split", "month_status"):
        return "time / bookkeeping", "derived", ""
    if col in ("capacity_max_hm3", "hydro_flag", "seasonal_share"):
        return "static feature", "BD-Embalses (seasonal_share: training years)", "hm3" if "hm3" in col else ""
    if col in ("si", "drought_state", "transfer_level"):
        return "label (current month)", "official rules (drought_rules.py)", ""
    if col.startswith(("state_h", "transfer_h", "pct_h")):
        return "target", "derived from label / storage h months ahead", "% of max capacity" if col.startswith("pct") else ""
    if col in rain_cols:
        return "rainfall feature", "CHIRPS v2.0", "mm" if "precip" in col else "SPI"
    if col in clim_cols:
        return "climate feature", "NOAA (NAO) / Univ. Barcelona (WeMO)", "index"
    if col.startswith(("stored_",)):
        return "storage", "BD-Embalses", "hm3"
    if col.startswith(("pct", "month_sin", "month_cos")):
        return "storage feature", "derived from BD-Embalses", "" if col.startswith("month_") else "% of max capacity"
    return "other", "", ""


card = pd.DataFrame([
    {"column": c, "role": describe(c)[0], "source": describe(c)[1], "unit": describe(c)[2],
     "dtype": str(df[c].dtype), "missing_pct": round(100 * df[c].isna().mean(), 1)}
    for c in df.columns])
card.to_csv(D2_TABLES / "data_card.csv", index=False)
print(f"\nData card: {len(card)} columns ->", card["role"].value_counts().to_dict())
