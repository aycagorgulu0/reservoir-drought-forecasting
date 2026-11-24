"""Step 30 (transformation): official labels for every reservoir-month.

Input : data/interim/reservoirs_monthly.csv   (step 11)
Output: data/interim/labels_monthly.csv
        reports/deliverable_2/tables/class_balance.csv
        reports/deliverable_2/tables/transfer_levels.csv

Labels
  si, drought_state   State Index from the monthly mean storage in hm3, for every reservoir
                      and system. The reference min/mean/max per calendar month come from the
                      training years only (1988-2016), so test months are never used to build
                      their own labels.
                      Storage in hm3 (not % full) is used because reported capacities change
                      (e.g. Contreras 874 -> 361 hm3 in 2019).
  transfer_level      Tajo-Segura level 1-4 from start-of-month Entrepeñas + Buendía storage
                      (system row only). The 12-month inflow condition of level 1 is not
                      applied yet: no inflow data.
"""
import numpy as np
import pandas as pd

from drought_rules import (STATES, TRANSFER_MONTHLY_HM3, drought_state, si_reference,
                           state_index, transfer_level)
from paths import D2_TABLES, LABELS_CSV, MONTHLY_CSV
from study_area import TRAIN_END, VALID_END

m = pd.read_csv(MONTHLY_CSV, parse_dates=["month"])
m["split"] = np.select([m["month"] <= TRAIN_END, m["month"] <= VALID_END],
                       ["train", "validation"], default="test")

# State Index with training-period reference values
ref = si_reference(m[m["split"] == "train"], "stored_mean_hm3")
m = m.merge(ref[["reservoir", "month_num", "v_min", "v_avg", "v_max"]],
            on=["reservoir", "month_num"], how="left")
m["si"] = state_index(m["stored_mean_hm3"], m["v_min"], m["v_avg"], m["v_max"])
m.loc[m["stored_mean_hm3"].isna() | m["v_avg"].isna(), "si"] = np.nan
m["drought_state"] = drought_state(m["si"])
m["drought_state_name"] = m["drought_state"].map(dict(enumerate(STATES)))

# Transfer level: Entrepeñas + Buendía system only
eb = m["reservoir"] == "Entrepeñas + Buendía"
m["transfer_level"] = np.nan
m.loc[eb, "transfer_level"] = transfer_level(m.loc[eb, "stored_first_hm3"], m.loc[eb, "month_num"])
m["transfer_hm3"] = m["transfer_level"].map(TRANSFER_MONTHLY_HM3)

cols = ["reservoir", "month", "split", "si", "drought_state", "drought_state_name",
        "transfer_level", "transfer_hm3"]
m[cols].to_csv(LABELS_CSV, index=False, float_format="%.4f")
print(f"Saved {LABELS_CSV.name}: {len(m):,} rows, SI available for {m['si'].notna().sum():,} "
      f"({m['si'].notna().mean():.1%}); no reference for {m.loc[m['si'].isna(), 'reservoir'].nunique()} series in some months")

# Class balance: study reservoirs, each system, per split
study = m[(m["role"] == "study") & ~m["is_system"]]
groups = {"Study reservoirs (114)": study,
          **{name: m[m["reservoir"] == name] for name in m.loc[m["is_system"], "reservoir"].unique()}}
rows = []
for group, g in groups.items():
    for split in ["train", "validation", "test", "all"]:
        s = g if split == "all" else g[g["split"] == split]
        counts = s["drought_state_name"].value_counts()
        n = counts.sum()
        rows.append({"group": group, "split": split, "months": int(n),
                     **{st: round(100 * counts.get(st, 0) / n, 1) if n else np.nan for st in STATES}})
balance = pd.DataFrame(rows)
balance.to_csv(D2_TABLES / "class_balance.csv", index=False)
print("\nDrought state distribution (% of months):")
print(balance.to_string(index=False))

# Transfer levels
t = m[eb].copy()
t["period"] = np.where(t["month"] >= "2014-10-01", "since Oct 2014 (rules in force)", "1988 - Sep 2014")
levels = (t.groupby(["period", "transfer_level"]).size().unstack(fill_value=0)
          .rename(columns=lambda c: f"level_{int(c)}"))
levels["months"] = levels.sum(axis=1)
levels.reset_index().to_csv(D2_TABLES / "transfer_levels.csv", index=False)
print("\nTransfer levels (months), Entrepeñas + Buendía:")
print(levels.to_string())
