"""Exploratory figures for the report annex (saved as PNG in figures/)."""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from paths import FIGURES as FIG, WEEKLY_CSV

# Palette and chart chrome (light mode, printed report)
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
BASIN_COLORS = {"Tajo": "#2a78d6", "Guadiana": "#eb6834", "Júcar": "#1baf7a"}
BLUE_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "axes.titlesize": 12,
    "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.titlecolor": INK,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.6,
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "legend.frameon": False,
})


def save(fig, name):
    fig.savefig(FIG / name, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


df = pd.read_csv(WEEKLY_CSV, parse_dates=["date"])
df = df[df["capacity_hm3"] > 0]  # drop placeholder rows (reservoir not yet in the bulletin)
df = df[df["date"] >= "1988-01-01"]  # first full year

focus = df[df["basin"].isin(BASIN_COLORS)]
basin_week = focus.groupby(["basin", "date"])[["stored_hm3", "capacity_hm3"]].sum()
basin_week["pct"] = 100 * basin_week["stored_hm3"] / basin_week["capacity_hm3"]
basin_week = basin_week.reset_index()

# 1. Entrepeñas + Buendía combined storage
eb = (df[df["reservoir"].isin(["Entrepeñas", "Buendía"])]
      .groupby("date")[["stored_hm3", "capacity_hm3"]].sum())
fig, ax = plt.subplots(figsize=(10, 4))
ax.fill_between(eb.index, eb["stored_hm3"], color=BASIN_COLORS["Tajo"], alpha=0.15, lw=0)
ax.plot(eb.index, eb["stored_hm3"], color=BASIN_COLORS["Tajo"], lw=1.6)
ax.axhline(eb["capacity_hm3"].max(), color=MUTED, lw=1, ls="--")
ax.text(eb.index[0], eb["capacity_hm3"].max() + 40, f"Total capacity {eb['capacity_hm3'].max():,.0f} hm³",
        color=INK2, fontsize=9)
for when, label, offset in [(eb["stored_hm3"].idxmin(), "Minimum", (0, 110)),
                            (eb["stored_hm3"].idxmax(), "Maximum", (-95, 25))]:
    v = eb.loc[when, "stored_hm3"]
    ax.plot(when, v, "o", ms=6, color=BASIN_COLORS["Tajo"], mec=SURFACE, mew=1.5)
    ax.annotate(f"{label}: {v:,.0f} hm³\n{when:%b %Y}", (when, v), xytext=offset,
                textcoords="offset points", ha="center", fontsize=9, color=INK,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
ax.set_ylim(0, eb["capacity_hm3"].max() * 1.12)
ax.set_ylabel("Stored water (hm³)")
ax.set_title("Entrepeñas + Buendía: combined storage, 1988-2026")
ax.xaxis.set_major_locator(mdates.YearLocator(4))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.margins(x=0.01)
save(fig, "fig1_entrepenas_buendia.png")

# 2. % full per focus basin over time (monthly mean, to reduce weekly noise)
fig, ax = plt.subplots(figsize=(10, 4.2))
ends = {}
for basin, color in BASIN_COLORS.items():
    s = (basin_week[basin_week["basin"] == basin].set_index("date")["pct"].resample("MS").mean())
    ax.plot(s.index, s.values, color=color, lw=1.6, label=basin)
    ends[basin] = (s.index[-1], s.values[-1])
# Direct end labels, pushed apart so they never overlap
placed = []
for basin, (x, y) in sorted(ends.items(), key=lambda kv: kv[1][1]):
    y = max(y, placed[-1] + 5) if placed else y
    placed.append(y)
    ax.text(x + pd.Timedelta(days=90), y, basin, color=INK, fontsize=9, va="center")
ax.set_ylim(0, 100)
ax.set_ylabel("% full (monthly mean)")
ax.set_title("Reservoir storage by basin: Tajo, Guadiana and Júcar")
ax.legend(loc="upper left", ncols=3)
ax.xaxis.set_major_locator(mdates.YearLocator(4))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.margins(x=0.01)
save(fig, "fig2_basins_pct_full.png")

# 3. Seasonal pattern: median and interquartile range across years, by week of year
fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharey=True)
for ax, (basin, color) in zip(axes, BASIN_COLORS.items()):
    b = basin_week[basin_week["basin"] == basin].copy()
    b["week"] = b["date"].dt.isocalendar().week.clip(upper=52)
    q = b.groupby("week")["pct"].quantile([0.25, 0.5, 0.75]).unstack()
    ax.fill_between(q.index, q[0.25], q[0.75], color=color, alpha=0.2, lw=0, label="25-75% of years")
    ax.plot(q.index, q[0.5], color=color, lw=2, label="Median")
    ax.set_title(basin, fontsize=11)
    ax.set_xticks([1, 14, 27, 40, 52], ["Jan", "Apr", "Jul", "Oct", "Dec"])
    ax.set_ylim(0, 100)
axes[0].set_ylabel("% full")
axes[0].legend(loc="lower left", fontsize=8)
fig.suptitle("Seasonal cycle: storage peaks in spring and bottoms out in autumn",
             x=0.01, ha="left", fontweight="bold", fontsize=12)
fig.tight_layout()
save(fig, "fig3_seasonal_pattern.png")

# 4. Annual mean % full per basin (heatmap): drought years stand out
annual = (basin_week.assign(year=basin_week["date"].dt.year)
          .groupby(["basin", "year"])["pct"].mean().unstack())
annual = annual.loc[list(BASIN_COLORS)]
fig, ax = plt.subplots(figsize=(11, 2.4))
im = ax.imshow(annual.values, aspect="auto", cmap=LinearSegmentedColormap.from_list("blue", BLUE_RAMP),
               vmin=0, vmax=100)
ax.set_yticks(range(len(annual)), annual.index)
years = annual.columns.tolist()
ax.set_xticks([i for i, y in enumerate(years) if y % 4 == 0], [y for y in years if y % 4 == 0])
ax.grid(False)
for s in ax.spines.values():
    s.set_visible(False)
ax.tick_params(length=0)
cb = fig.colorbar(im, ax=ax, pad=0.01, fraction=0.025)
cb.set_label("Annual mean % full", color=INK2)
cb.outline.set_visible(False)
ax.set_title("Annual mean storage by basin: low years mark drought periods")
save(fig, "fig4_annual_heatmap.png")

# 5. Data coverage: reservoirs reporting each year
cov = df.groupby(df["date"].dt.year)["reservoir"].nunique()
fig, ax = plt.subplots(figsize=(10, 3.2))
ax.bar(cov.index, cov.values, width=0.8, color="#2a78d6")
ax.set_ylabel("Reservoirs reporting")
ax.set_title("Data coverage: number of reservoirs in the bulletin per year (all Spain)")
ax.set_xlim(cov.index.min() - 0.8, cov.index.max() + 0.8)
for year in [cov.index.min(), 1999, cov.index.max()]:
    if year in cov.index:
        ax.text(year, cov[year] + 4, str(cov[year]), ha="center", fontsize=8, color=INK2)
ax.set_ylim(0, cov.max() * 1.12)
save(fig, "fig5_coverage.png")
