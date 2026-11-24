"""Step 10 (preprocessing): select the study area and clean the weekly reservoir series.

Input : data/interim/reservoirs_spain_weekly.csv   (step 01, all of Spain)
Output: data/interim/reservoirs_weekly_clean.csv   (study + reference basins, cleaned)
        data/processed/reservoirs.csv              (one row per reservoir: metadata)
        reports/deliverable_2/tables/cleaning_log.csv

Every step records how many rows and reservoirs it affects, so the report can quote
the cleaning table directly. Storage values judged wrong are set to missing and then
filled by linear interpolation over at most MAX_GAP_WEEKS; a flag column marks them.
"""
import numpy as np
import pandas as pd

from paths import D2_TABLES, RESERVOIRS_CSV, WEEKLY_CLEAN_CSV, WEEKLY_CSV
from study_area import ALL_BASINS, KEY_RESERVOIRS, STUDY_BASINS

START = "1988-01-01"        # the only earlier week (6 Oct 1987) is followed by a 12-week gap
SURCHARGE_MAX = 1.20        # stored/capacity up to 1.2: plausible flood surcharge -> cap at 100%
SPIKE_JUMP = 0.20           # one-week spike: value differs from both neighbours by > 20% of capacity...
SPIKE_NEIGHBOURS = 0.05     # ...while the two neighbours agree within 5% of capacity
MAX_GAP_WEEKS = 4           # longest run of missing weeks filled by interpolation

log = []


def record(step, action, affected_rows, df, affected_reservoirs=None):
    log.append({
        "step": step,
        "action": action,
        "rows_affected": int(affected_rows),
        "reservoirs_affected": None if affected_reservoirs is None else int(affected_reservoirs),
        "rows_after": len(df),
        "reservoirs_after": df["reservoir"].nunique(),
    })
    print(f"{step:<28} {action:<70} rows={affected_rows:>7,}  -> {len(df):>8,} rows")


df = pd.read_csv(WEEKLY_CSV, parse_dates=["date"])
record("0 input", "Weekly bulletin, all of Spain (step 01)", 0, df)

# 1. Data selection: study basins (Tajo, Guadiana, Júcar) + reference basin (Duero)
n = len(df)
df = df[df["basin"].isin(ALL_BASINS)].copy()
record("1 select basins", f"Keep {', '.join(ALL_BASINS)}; drop the other 12 basins", n - len(df), df)
df["role"] = np.where(df["basin"].isin(STUDY_BASINS), "study", "reference")

# 2. Isolated first week
n = len(df)
df = df[df["date"] >= START]
record("2 start date", "Drop the isolated week of 6 Oct 1987 (followed by a 12-week gap)", n - len(df), df)

# 3. Placeholder rows: capacity = 0 means the reservoir was not yet in the bulletin
ph = df["capacity_hm3"].fillna(0) == 0
res = df.loc[ph, "reservoir"].nunique()
df = df[~ph].copy()
record("3 placeholders", "Drop rows with capacity = 0 (reservoir not yet reported)", ph.sum(), df, res)

# 4. Remaining missing storage values (none expected after step 3; kept for safety)
na = df["stored_hm3"].isna()
record("4 missing values", "Missing storage values left after steps 1-3", na.sum(), df, df.loc[na, "reservoir"].nunique())

df = df.sort_values(["reservoir", "date"]).reset_index(drop=True)
df["flag_surcharge"] = 0
df["flag_imputed"] = 0
ratio = df["stored_hm3"] / df["capacity_hm3"]

# 5. Storage above capacity
surcharge = (ratio > 1) & (ratio <= SURCHARGE_MAX)
df.loc[surcharge, "flag_surcharge"] = 1
df.loc[surcharge, "stored_hm3"] = df.loc[surcharge, "capacity_hm3"]
record("5a surcharge", f"Storage 100-{SURCHARGE_MAX:.0%} of capacity: cap at 100%, flag",
       surcharge.sum(), df, df.loc[surcharge, "reservoir"].nunique())

impossible = ratio > SURCHARGE_MAX
df.loc[impossible, "stored_hm3"] = np.nan
record("5b impossible values", f"Storage > {SURCHARGE_MAX:.0%} of capacity (up to 7x): set missing",
       impossible.sum(), df, df.loc[impossible, "reservoir"].nunique())

# 6. Isolated zeros: one zero reading between two positive readings
g = df.groupby("reservoir")["stored_hm3"]
prev, nxt = g.shift(1), g.shift(-1)
iso_zero = (df["stored_hm3"] == 0) & (prev > 0) & (nxt > 0)
df.loc[iso_zero, "stored_hm3"] = np.nan
record("6 isolated zeros", "Single zero reading between positive readings: set missing",
       iso_zero.sum(), df, df.loc[iso_zero, "reservoir"].nunique())

# 7. One-week spikes: a reading far from both neighbours, which agree with each other
g = df.groupby("reservoir")["stored_hm3"]
prev, nxt = g.shift(1), g.shift(-1)
cap, x = df["capacity_hm3"], df["stored_hm3"]
spike = (((x - prev).abs() > SPIKE_JUMP * cap) & ((x - nxt).abs() > SPIKE_JUMP * cap)
         & ((prev - nxt).abs() < SPIKE_NEIGHBOURS * cap) & ((x - prev) * (x - nxt) > 0))
df.loc[spike, "stored_hm3"] = np.nan
record("7 one-week spikes",
       f"Jump > {SPIKE_JUMP:.0%} of capacity away and back within a week: set missing",
       spike.sum(), df, df.loc[spike, "reservoir"].nunique())

# 8. Interpolate the values set missing (linear in time, short gaps only)
missing = df["stored_hm3"].isna()
df["stored_hm3"] = (df.set_index("date").groupby("reservoir")["stored_hm3"]
                    .transform(lambda s: s.interpolate(method="time", limit=MAX_GAP_WEEKS,
                                                       limit_area="inside"))
                    .to_numpy())
filled = missing & df["stored_hm3"].notna()
df.loc[filled, "flag_imputed"] = 1
record("8 interpolation", f"Fill missing storage by linear interpolation (gaps <= {MAX_GAP_WEEKS} weeks)",
       filled.sum(), df, df.loc[filled, "reservoir"].nunique())

n = len(df)
df = df[df["stored_hm3"].notna()].copy()
record("9 unfilled", "Drop values that could not be interpolated", n - len(df), df)

# 10. Capacity changes: keep the reported capacity per row, add the reservoir's maximum
n_changes = df.groupby("reservoir")["capacity_hm3"].nunique()
df["capacity_max_hm3"] = df.groupby("reservoir")["capacity_hm3"].transform("max")
df["pct_full"] = 100 * df["stored_hm3"] / df["capacity_hm3"]
df["pct_full_max"] = 100 * df["stored_hm3"] / df["capacity_max_hm3"]
# (e.g. Contreras: 874 -> 852 hm3 in 2009, then limited to 361 hm3 from Nov 2019; storage never
# exceeds the reported value, so it is the operating limit, not an error)
record("10 capacity changes", "Rows of reservoirs whose reported capacity changes (kept; add pct_full_max)",
       df["reservoir"].isin(n_changes[n_changes > 1].index).sum(), df, (n_changes > 1).sum())

cols = ["basin", "role", "reservoir", "date", "capacity_hm3", "capacity_max_hm3", "stored_hm3",
        "pct_full", "pct_full_max", "hydro_flag", "flag_surcharge", "flag_imputed"]
df = df[cols]
df.to_csv(WEEKLY_CLEAN_CSV, index=False, float_format="%.3f")
record("11 output", "Clean weekly table", 0, df)

# Reservoir metadata (one row per reservoir), used by later steps and the data card
latest = df["date"].max()
meta = (df.groupby(["basin", "role", "reservoir"])
        .agg(capacity_latest_hm3=("capacity_hm3", "last"),
             capacity_max_hm3=("capacity_max_hm3", "first"),
             capacity_changes=("capacity_hm3", "nunique"),
             hydro_flag=("hydro_flag", "max"),
             first_date=("date", "min"),
             last_date=("date", "max"),
             weeks=("date", "size"),
             weeks_imputed=("flag_imputed", "sum"),
             weeks_surcharge=("flag_surcharge", "sum"))
        .reset_index())
meta["capacity_changes"] -= 1
meta["active"] = meta["last_date"] == latest
meta["key_reservoir"] = meta["reservoir"].isin(KEY_RESERVOIRS)
meta.to_csv(RESERVOIRS_CSV, index=False)

pd.DataFrame(log).to_csv(D2_TABLES / "cleaning_log.csv", index=False)

print(f"\nSaved {WEEKLY_CLEAN_CSV.name}: {len(df):,} rows, {df['reservoir'].nunique()} reservoirs")
print(meta.groupby(["role", "basin"]).agg(reservoirs=("reservoir", "size"),
                                          capacity_hm3=("capacity_latest_hm3", "sum")).to_string())
print("\nKey reservoirs:")
print(meta[meta["key_reservoir"]][["reservoir", "capacity_latest_hm3", "capacity_max_hm3",
                                   "capacity_changes", "first_date", "weeks_imputed"]].to_string(index=False))
