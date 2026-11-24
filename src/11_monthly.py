"""Step 11 (preprocessing): aggregate the clean weekly series to months and build the combined systems.

Input : data/interim/reservoirs_weekly_clean.csv   (step 10)
Output: data/interim/reservoirs_monthly.csv
        reports/deliverable_2/tables/monthly_summary.csv

Per reservoir and month we keep three readings of storage, each needed later:
  stored_first_hm3  first weekly reading of the month: the Tajo-Segura transfer rules use
                    the storage at the start of each month
  stored_mean_hm3   mean of the weekly readings: the main forecasting target
  stored_last_hm3   last weekly reading: end-of-month state

Every reservoir gets a complete monthly calendar from its first to its last report.
Months without any reading are filled by linear interpolation when the gap is at most
MAX_GAP_MONTHS long, and left missing otherwise (month_status says which).

The combined systems (Entrepeñas + Buendía, Alarcón + Contreras) are added as extra rows
(is_system = True); they exist only in months where every member has a value.
"""
import numpy as np
import pandas as pd

from paths import D2_TABLES, MONTHLY_CSV, WEEKLY_CLEAN_CSV
from study_area import SYSTEMS

MAX_GAP_MONTHS = 2
LOW_COVERAGE_WEEKS = 2   # months with fewer weekly readings than this are flagged

w = pd.read_csv(WEEKLY_CLEAN_CSV, parse_dates=["date"])
w["month"] = w["date"].dt.to_period("M")
w = w.sort_values(["reservoir", "date"])

keys = ["basin", "role", "reservoir"]
m = (w.groupby(keys + ["month"])
     .agg(stored_first_hm3=("stored_hm3", "first"),
          stored_mean_hm3=("stored_hm3", "mean"),
          stored_last_hm3=("stored_hm3", "last"),
          capacity_hm3=("capacity_hm3", "last"),
          capacity_max_hm3=("capacity_max_hm3", "first"),
          hydro_flag=("hydro_flag", "max"),
          n_weeks=("date", "size"),
          n_weeks_imputed=("flag_imputed", "sum"),
          any_surcharge=("flag_surcharge", "max"))
     .reset_index())
print(f"Reservoir-months with readings: {len(m):,}")

# Complete monthly calendar per reservoir
STORED = ["stored_first_hm3", "stored_mean_hm3", "stored_last_hm3"]
frames = []
for (basin, role, res), g in m.groupby(keys):
    g = g.set_index("month")
    full = pd.period_range(g.index.min(), g.index.max(), freq="M")
    g = g.reindex(full)
    observed = g["n_weeks"].notna()
    g[STORED] = g[STORED].interpolate(limit=MAX_GAP_MONTHS, limit_area="inside")
    for c in ["capacity_hm3", "capacity_max_hm3", "hydro_flag"]:
        g[c] = g[c].ffill()
    g["n_weeks"] = g["n_weeks"].fillna(0)
    g["n_weeks_imputed"] = g["n_weeks_imputed"].fillna(0)
    g["any_surcharge"] = g["any_surcharge"].fillna(0)
    g["month_status"] = np.where(observed, "observed",
                                 np.where(g["stored_mean_hm3"].notna(), "interpolated", "missing"))
    g[["basin", "role", "reservoir"]] = basin, role, res
    frames.append(g.rename_axis("month").reset_index())
m = pd.concat(frames, ignore_index=True)
m["is_system"] = False

# Combined systems
sys_rows = []
for name, spec in SYSTEMS.items():
    parts = m[m["reservoir"].isin(spec["members"])]
    ok = parts.groupby("month")["stored_mean_hm3"].count() == len(spec["members"])
    parts = parts[parts["month"].isin(ok[ok].index)]
    agg = (parts.groupby("month")
           .agg(stored_first_hm3=("stored_first_hm3", "sum"),
                stored_mean_hm3=("stored_mean_hm3", "sum"),
                stored_last_hm3=("stored_last_hm3", "sum"),
                capacity_hm3=("capacity_hm3", "sum"),
                capacity_max_hm3=("capacity_max_hm3", "sum"),
                hydro_flag=("hydro_flag", "max"),
                n_weeks=("n_weeks", "min"),
                n_weeks_imputed=("n_weeks_imputed", "sum"),
                any_surcharge=("any_surcharge", "max"),
                n_interp=("month_status", lambda s: (s != "observed").sum()))
           .reset_index())
    agg["month_status"] = np.where(agg.pop("n_interp") > 0, "interpolated", "observed")
    agg[["basin", "role", "reservoir", "is_system"]] = spec["basin"], "study", name, True
    sys_rows.append(agg)
    print(f"System {name}: {len(agg)} months")
m = pd.concat([m] + sys_rows, ignore_index=True)

# Derived columns
m["pct_full_mean"] = 100 * m["stored_mean_hm3"] / m["capacity_hm3"]
m["pct_full_first"] = 100 * m["stored_first_hm3"] / m["capacity_hm3"]
m["pct_full_max_mean"] = 100 * m["stored_mean_hm3"] / m["capacity_max_hm3"]
m["low_coverage"] = (m["month_status"] == "observed") & (m["n_weeks"] < LOW_COVERAGE_WEEKS)
m["year"] = m["month"].dt.year
m["month_num"] = m["month"].dt.month
m["month"] = m["month"].dt.to_timestamp()  # first day of the month

cols = ["basin", "role", "reservoir", "is_system", "month", "year", "month_num",
        "capacity_hm3", "capacity_max_hm3", "hydro_flag",
        "stored_first_hm3", "stored_mean_hm3", "stored_last_hm3",
        "pct_full_first", "pct_full_mean", "pct_full_max_mean",
        "n_weeks", "n_weeks_imputed", "any_surcharge", "month_status", "low_coverage"]
m = m[cols].sort_values(["is_system", "basin", "reservoir", "month"])
m.to_csv(MONTHLY_CSV, index=False, float_format="%.3f")

# Summary for the report
single = m[~m["is_system"]]
summary = (single.groupby(["role", "basin"])
           .agg(reservoirs=("reservoir", "nunique"),
                reservoir_months=("month", "size"),
                observed=("month_status", lambda s: (s == "observed").sum()),
                interpolated=("month_status", lambda s: (s == "interpolated").sum()),
                missing=("month_status", lambda s: (s == "missing").sum()),
                low_coverage=("low_coverage", "sum"))
           .reset_index())
total = summary.drop(columns=["role", "basin"]).sum()
summary = pd.concat([summary, pd.DataFrame([{"role": "all", "basin": "all", **total.to_dict()}])],
                    ignore_index=True)
summary.to_csv(D2_TABLES / "monthly_summary.csv", index=False)

print(f"\nSaved {MONTHLY_CSV.name}: {len(m):,} rows "
      f"({len(single):,} reservoir-months + {m['is_system'].sum()} system-months)")
print(summary.to_string(index=False))

eb = m[m["reservoir"] == "Entrepeñas + Buendía"].set_index("month")["stored_first_hm3"]
print(f"\nEntrepeñas + Buendía, start-of-month storage: min {eb.min():.0f} hm3 ({eb.idxmin():%b %Y}), "
      f"max {eb.max():.0f} hm3 ({eb.idxmax():%b %Y}), latest {eb.iloc[-1]:.0f} hm3 ({eb.index[-1]:%b %Y})")
