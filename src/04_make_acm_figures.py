"""Column-width versions of figures 1 and 3 for the ACM two-column report (drawn at print size)."""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from paths import FIGURES as FIG, WEEKLY_CSV

INK, INK2, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BASIN_COLORS = {"Tajo": "#2a78d6", "Guadiana": "#eb6834", "Júcar": "#1baf7a"}
COL_IN = 3.33  # ACM column width

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 7, "text.color": INK,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "axes.titlesize": 7.5, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.5,
    "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelcolor": INK2, "ytick.labelcolor": INK2, "legend.frameon": False, "legend.fontsize": 6.5,
    "lines.linewidth": 1.1,
})

df = pd.read_csv(WEEKLY_CSV, parse_dates=["date"])
df = df[(df["capacity_hm3"] > 0) & (df["date"] >= "1988-01-01")]

# Figure 1: Entrepeñas + Buendía combined storage
eb = (df[df["reservoir"].isin(["Entrepeñas", "Buendía"])]
      .groupby("date")[["stored_hm3", "capacity_hm3"]].sum())
fig, ax = plt.subplots(figsize=(COL_IN, 1.9))
ax.fill_between(eb.index, eb["stored_hm3"], color=BASIN_COLORS["Tajo"], alpha=0.15, lw=0)
ax.plot(eb.index, eb["stored_hm3"], color=BASIN_COLORS["Tajo"], lw=0.9)
cap = eb["capacity_hm3"].max()
ax.axhline(cap, color=MUTED, lw=0.7, ls="--")
ax.text(eb.index[-1], cap + 50, f"Capacity {cap:,.0f} hm³", color=INK2, fontsize=6, ha="right")
lo, hi = eb["stored_hm3"].idxmin(), eb["stored_hm3"].idxmax()
for when, label, off in [(lo, "Min", (4, 80)), (hi, "Max", (-48, 4))]:
    v = eb.loc[when, "stored_hm3"]
    ax.plot(when, v, "o", ms=3, color=BASIN_COLORS["Tajo"])
    ax.annotate(f"{label} {v:,.0f} hm³\n{when:%b %Y}", (when, v), xytext=off, textcoords="offset points",
                fontsize=6, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.5))
ax.set_ylim(0, cap * 1.15)
ax.set_ylabel("Stored water (hm³)")
ax.xaxis.set_major_locator(mdates.YearLocator(8))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.margins(x=0.01)
fig.savefig(FIG / "acm_fig1_entrepenas_buendia.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)

# Figure 2: seasonal cycle per basin (median and middle 50% of years)
focus = df[df["basin"].isin(BASIN_COLORS)]
bw = focus.groupby(["basin", "date"])[["stored_hm3", "capacity_hm3"]].sum().reset_index()
bw["pct"] = 100 * bw["stored_hm3"] / bw["capacity_hm3"]
fig, axes = plt.subplots(1, 3, figsize=(COL_IN, 1.75), sharey=True)
for ax, (basin, color) in zip(axes, BASIN_COLORS.items()):
    b = bw[bw["basin"] == basin].copy()
    b["week"] = b["date"].dt.isocalendar().week.clip(upper=52)
    q = b.groupby("week")["pct"].quantile([0.25, 0.5, 0.75]).unstack()
    ax.fill_between(q.index, q[0.25], q[0.75], color=color, alpha=0.22, lw=0)
    ax.plot(q.index, q[0.5], color=color, lw=1.2)
    ax.set_title(basin)
    ax.set_xticks([1, 27, 52], ["Jan", "Jul", "Dec"])
    ax.set_ylim(0, 100)
axes[0].set_ylabel("% full")
fig.tight_layout(w_pad=0.4)
fig.savefig(FIG / "acm_fig2_seasonal.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("saved acm figures")
