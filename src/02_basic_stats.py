"""Basic descriptive statistics of the reservoir dataset, for the report's data section and annex."""

import pandas as pd

from paths import WEEKLY_CSV

df = pd.read_csv(WEEKLY_CSV, parse_dates=["date"])

print("Rows:", f"{len(df):,}")
print("Date range:", df["date"].min().date(), "->", df["date"].max().date())
print("Weeks:", df["date"].nunique())
print("Basins:", df["basin"].nunique(), "| Reservoirs:", df["reservoir"].nunique())
print("\nMissing values:\n", df.isna().sum())
print("\nRows with missing capacity, by year:\n",
      df[df["capacity_hm3"].isna()].groupby(df["date"].dt.year).size().to_string())
print("\nStored > capacity:", (df["stored_hm3"] > df["capacity_hm3"]).sum())

last = df[df["date"] == df["date"].max()]
print("\nTotal capacity (latest week): %.0f hm3 | stored: %.0f hm3 (%.1f%%)" % (
    last["capacity_hm3"].sum(), last["stored_hm3"].sum(),
    100 * last["stored_hm3"].sum() / last["capacity_hm3"].sum()))

per_basin = (last.groupby("basin")
             .agg(reservoirs=("reservoir", "nunique"),
                  capacity_hm3=("capacity_hm3", "sum"),
                  stored_hm3=("stored_hm3", "sum")))
per_basin["pct_full"] = (100 * per_basin["stored_hm3"] / per_basin["capacity_hm3"]).round(1)
print("\nPer basin (latest week):\n", per_basin.sort_values("capacity_hm3", ascending=False).to_string())

focus = df[df["basin"].str.contains("Tajo|Guadiana|J.car", regex=True)]
print("\nFocus basins (Tajo, Guadiana, Júcar): %d reservoirs, %s rows" % (
    focus["reservoir"].nunique(), f"{len(focus):,}"))

key = ["Entrepeñas", "Buendía", "Alarcón", "Contreras"]
print("\nKey reservoirs:")
for name in key:
    r = df[df["reservoir"].str.contains(name, case=False)]
    print(f"  {name}: matches={r['reservoir'].unique().tolist()}, rows={len(r)}, "
          f"capacity={r['capacity_hm3'].max()}, min%={r['pct_full'].min()}, max%={r['pct_full'].max()}")

eb = df[df["reservoir"].isin(["Entrepeñas", "Buendía"])].groupby("date")[["stored_hm3", "capacity_hm3"]].sum()
print("\nEntrepeñas+Buendía combined: min %.0f hm3 (%s), max %.0f hm3 (%s), latest %.0f hm3" % (
    eb["stored_hm3"].min(), eb["stored_hm3"].idxmin().date(),
    eb["stored_hm3"].max(), eb["stored_hm3"].idxmax().date(), eb["stored_hm3"].iloc[-1]))
