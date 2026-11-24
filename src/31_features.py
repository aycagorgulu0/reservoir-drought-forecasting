"""Step 31 (transformation): storage features and forecast targets for every reservoir-month.

Input : data/interim/reservoirs_monthly.csv, data/interim/labels_monthly.csv
Output: data/interim/features_monthly.csv
        reports/deliverable_2/tables/seasonal_share.csv

A row describes what is known at the end of month t; targets are h months later.

Main series: pct = monthly mean storage as % of the largest capacity ever reported
(pct_full_max_mean), so capacity changes do not appear as jumps.

Features
  pct_lag1..lag12, lag24, lag36   past storage (Baron et al. use up to 12; 24 and 36 test H1-H2)
  pct_diff1, diff3, diff12        recent changes
  pct_mean3..mean36, pct_std12    rolling level and variability
  pct_clim, pct_anom              training-years average for this calendar month, and the
                                  current departure from it (Baron: 2nd most important feature)
  month_sin, month_cos            month on a circle
  seasonal_share                  per reservoir, training years only (H1, H4)
  capacity_max_hm3, hydro_flag    static
Targets
  pct_h1, pct_h3, pct_h6          storage 1, 3, 6 months ahead (objective O1)
  state_h1, state_h3, state_h6    drought state 1, 3, 6 months ahead (O2)
  transfer_h1, h3, h6             transfer level ahead, Entrepeñas + Buendía only (O2)
"""
import numpy as np
import pandas as pd

from features import (climatology, diffs, lags, leads, month_cycle, rolling_means,
                      rolling_std, seasonal_share)
from paths import D2_TABLES, FEATURES_CSV, LABELS_CSV, MONTHLY_CSV
from study_area import TRAIN_END

HORIZONS = [1, 3, 6]

m = pd.read_csv(MONTHLY_CSV, parse_dates=["month"])
lab = pd.read_csv(LABELS_CSV, parse_dates=["month"])
df = (m.merge(lab, on=["reservoir", "month"], how="left")
      .sort_values(["reservoir", "month"]).reset_index(drop=True))
df["pct"] = df["pct_full_max_mean"]
train = df[df["month"] <= TRAIN_END]

clim = climatology(train, "pct")
share = seasonal_share(train, "pct")
df = df.merge(clim, on=["reservoir", "month_num"], how="left").merge(share, on="reservoir", how="left")
df["pct_anom"] = df["pct"] - df["pct_clim"]

parts = [
    lags(df, "pct", list(range(1, 13)) + [24, 36]),
    diffs(df, "pct", [1, 3, 12]),
    rolling_means(df, "pct", [3, 6, 12, 24, 36]),
    rolling_std(df, "pct", 12).to_frame(),
    month_cycle(df["month_num"]),
    leads(df, "pct", HORIZONS),
    leads(df, "drought_state", HORIZONS).rename(columns=lambda c: c.replace("drought_state", "state")),
    leads(df, "transfer_level", HORIZONS).rename(columns=lambda c: c.replace("transfer_level", "transfer")),
]
df = pd.concat([df] + parts, axis=1)

keep = (["basin", "role", "reservoir", "is_system", "month", "year", "month_num", "split",
         "month_status", "capacity_max_hm3", "hydro_flag", "seasonal_share",
         "pct", "stored_mean_hm3", "stored_first_hm3", "si", "drought_state", "transfer_level",
         "pct_clim", "pct_anom"]
        + [c for p in parts for c in p.columns])
df = df[keep]
df.to_csv(FEATURES_CSV, index=False, float_format="%.4f")
print(f"Saved {FEATURES_CSV.name}: {len(df):,} rows x {df.shape[1]} columns")

# Seasonal share table for the report (median per basin + key reservoirs and systems)
meta = df.drop_duplicates("reservoir")[["basin", "role", "reservoir", "is_system", "seasonal_share"]]
by_basin = (meta[~meta["is_system"]].groupby(["role", "basin"])["seasonal_share"]
            .agg(reservoirs="count", median="median").reset_index())
key = meta[meta["reservoir"].isin(["Entrepeñas", "Buendía", "Alarcón", "Contreras",
                                   "Entrepeñas + Buendía", "Alarcón + Contreras"])]
table = pd.concat([by_basin.rename(columns={"basin": "name"}),
                   key[["reservoir", "seasonal_share"]].rename(columns={"reservoir": "name",
                                                                         "seasonal_share": "median"})],
                  ignore_index=True)
table["median"] = table["median"].round(3)
table.to_csv(D2_TABLES / "seasonal_share.csv", index=False)
print("\nSeasonal share (training years 1988-2016):")
print(table.to_string(index=False))

# Coverage of the main inputs and targets
check = ["pct_lag12", "pct_lag36", "pct_mean36", "pct_h1", "pct_h6", "state_h6"]
print("\nNon-missing share:", {c: f"{df[c].notna().mean():.1%}" for c in check})
