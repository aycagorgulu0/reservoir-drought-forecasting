"""Step 33 (exploration): check that the transformed data supports the hypotheses.

Input : data/processed/model_table.csv.gz   (step 32)
Output: reports/deliverable_2/tables/memory.csv            per basin: seasonal share, autocorrelation, best SPI
        reports/deliverable_2/tables/spi_correlation.csv   median corr(storage anomaly, SPI-k)
        reports/deliverable_2/tables/clusters.csv          k-means preview (silhouette, profile)
        reports/deliverable_2/tables/state_persistence.csv how often the label changes in h months
        data/processed/reservoir_profiles.csv              one row per reservoir: behaviour + cluster
        figures/fig_d2_spi_correlation.png, figures/fig_d2_clusters.png

H1/H2  If storage is hyperannual, its anomaly (storage minus the usual level for that calendar
       month) should keep memory beyond 12 months and follow rainfall accumulated over long
       windows (24-36 months).
H3     The drought state must change often enough within 1-6 months to be worth forecasting.
H4     Reservoirs should split into seasonal and hyperannual groups.
Only training years (1988-2016) and reservoirs with >= 10 years of data are used.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from drought_rules import STATES
from paths import D2_TABLES, FIGURES, MODEL_TABLE, PROCESSED
from study_area import KEY_RESERVOIRS

SPI_K = [3, 6, 12, 24, 36]
MIN_MONTHS = 120
BASINS = ["Duero", "Tajo", "Guadiana", "Júcar"]
COLORS = {"Duero": "#7f7f7f", "Tajo": "#1f77b4", "Guadiana": "#2ca02c", "Júcar": "#d62728"}

df = pd.read_csv(MODEL_TABLE, parse_dates=["month"])
tr = df[(df["split"] == "train") & ~df["is_system"]].dropna(subset=["pct"])
size = tr.groupby("reservoir").size()
tr = tr[tr["reservoir"].isin(size[size >= MIN_MONTHS].index)].sort_values(["reservoir", "month"])

# ------------------------------------------------------------ behaviour profile per reservoir
rows = []
for (basin, res), g in tr.groupby(["basin", "reservoir"]):
    x = g.set_index("month")["pct_anom"].asfreq("MS")  # anomaly: the yearly cycle is removed
    row = {"basin": basin, "reservoir": res, "months": len(g),
           "seasonal_share": g["seasonal_share"].iloc[0],
           "cycle_amplitude": g.groupby("month_num")["pct"].mean().pipe(lambda c: c.max() - c.min()),
           "interannual_sd": g.groupby("year")["pct"].mean().std(),
           "acf_12": x.autocorr(12), "acf_24": x.autocorr(24)}
    for k in SPI_K:
        row[f"corr_spi_{k}"] = g["pct_anom"].corr(g[f"spi_{k}"])
    corrs = {k: row[f"corr_spi_{k}"] for k in SPI_K if pd.notna(row[f"corr_spi_{k}"])}
    row["best_spi"] = max(corrs, key=corrs.get) if corrs else np.nan
    rows.append(row)
prof = pd.DataFrame(rows)

memory = (prof.groupby("basin")
          .agg(reservoirs=("reservoir", "size"), seasonal_share=("seasonal_share", "median"),
               acf_12=("acf_12", "median"), acf_24=("acf_24", "median"),
               best_spi_median=("best_spi", "median"),
               share_best_24_36=("best_spi", lambda s: (s >= 24).mean()))
          .reindex(BASINS).round(2).reset_index())
memory.to_csv(D2_TABLES / "memory.csv", index=False)

corr_cols = [f"corr_spi_{k}" for k in SPI_K]
corr = prof.groupby("basin")[corr_cols].median().reindex(BASINS)
key = prof.set_index("reservoir").reindex(KEY_RESERVOIRS)[corr_cols]
pd.concat([corr, key]).round(2).to_csv(D2_TABLES / "spi_correlation.csv")

# ------------------------------------------------------------ H3: how often the state changes
pers = []
for h in (1, 3, 6):
    for name, sub in [("Study reservoirs", df[(df["role"] == "study") & ~df["is_system"]]),
                      ("Alarcón + Contreras", df[df["reservoir"] == "Alarcón + Contreras"]),
                      ("Entrepeñas + Buendía", df[df["reservoir"] == "Entrepeñas + Buendía"])]:
        s = sub.dropna(subset=["drought_state", f"state_h{h}"])
        pers.append({"series": name, "horizon": h, "months": len(s),
                     "changed": round((s["drought_state"] != s[f"state_h{h}"]).mean(), 3)})
    t = df[df["reservoir"] == "Entrepeñas + Buendía"].dropna(subset=["transfer_level", f"transfer_h{h}"])
    pers.append({"series": "Transfer level", "horizon": h, "months": len(t),
                 "changed": round((t["transfer_level"] != t[f"transfer_h{h}"]).mean(), 3)})
pers = pd.DataFrame(pers)
pers.to_csv(D2_TABLES / "state_persistence.csv", index=False)

# ------------------------------------------------------------ H4: clustering preview
FEATS = ["seasonal_share", "cycle_amplitude", "interannual_sd", "acf_12", "acf_24"]
data = prof.dropna(subset=FEATS).reset_index(drop=True)
X = StandardScaler().fit_transform(data[FEATS])
sil = pd.DataFrame([{"k": k, "silhouette": round(silhouette_score(
    X, KMeans(n_clusters=k, n_init=20, random_state=0).fit_predict(X)), 3)} for k in range(2, 7)])
best_k = int(sil.loc[sil["silhouette"].idxmax(), "k"])
lab = KMeans(n_clusters=best_k, n_init=20, random_state=0).fit_predict(X)
ward = fcluster(linkage(X, "ward"), best_k, "maxclust")
ari = adjusted_rand_score(lab, ward)
order = pd.Series(data["seasonal_share"]).groupby(lab).median().sort_values().index  # 0 = most hyperannual
data["cluster"] = pd.Series(lab).map({c: i for i, c in enumerate(order)})
profile = (data.groupby("cluster")
           .agg(reservoirs=("reservoir", "size"), seasonal_share=("seasonal_share", "median"),
                acf_24=("acf_24", "median"), interannual_sd=("interannual_sd", "median"),
                **{b.lower(): ("basin", lambda s, b=b: int((s == b).sum())) for b in BASINS})
           .round(2).reset_index())
with open(D2_TABLES / "clusters.csv", "w", encoding="utf-8") as f:
    sil.to_csv(f, index=False)
    f.write(f"\nbest_k,{best_k}\nward_vs_kmeans_ari,{ari:.2f}\n\n")
    profile.to_csv(f, index=False)
data.to_csv(PROCESSED / "reservoir_profiles.csv", index=False, float_format="%.3f")

# ------------------------------------------------------------ figures (ACM column width)
plt.rcParams.update({"font.size": 7})
fig, ax = plt.subplots(figsize=(3.3, 2.0))
for b in BASINS:
    ax.plot(SPI_K, corr.loc[b].values, marker="o", ms=3, lw=1.2, color=COLORS[b],
            ls="--" if b == "Duero" else "-",
            label=f"{b} ({int(memory.set_index('basin').loc[b, 'reservoirs'])})")
ax.set_xticks(SPI_K)
ax.set_xlabel("SPI accumulation window (months)")
ax.set_ylabel("Median corr. with\nstorage anomaly")
ax.grid(alpha=0.3, lw=0.5)
ax.legend(frameon=False, fontsize=6)
fig.tight_layout()
fig.savefig(FIGURES / "fig_d2_spi_correlation.png", dpi=300)
plt.close(fig)

fig, ax = plt.subplots(figsize=(3.3, 2.1))
marks = {"Duero": "o", "Tajo": "s", "Guadiana": "^", "Júcar": "D"}
ccol = ["#d62728", "#1f77b4", "#2ca02c", "#9467bd", "#ff7f0e", "#8c564b"]
for b in BASINS:
    s = data[data["basin"] == b]
    ax.scatter(s["seasonal_share"], s["acf_24"], s=10, marker=marks[b], edgecolors="none", alpha=0.85,
               c=[ccol[c] for c in s["cluster"]])
    ax.scatter([], [], marker=marks[b], c="k", s=10, label=b)
for name in KEY_RESERVOIRS:
    r = data[data["reservoir"] == name]
    if len(r):
        ax.annotate(name, (r["seasonal_share"].iloc[0], r["acf_24"].iloc[0]), fontsize=5.5,
                    xytext=(3, 2), textcoords="offset points")
ax.set_xlabel("Seasonal share of storage variance")
ax.set_ylabel("Autocorrelation at 24 months")
ax.grid(alpha=0.3, lw=0.5)
ax.legend(frameon=False, fontsize=6, loc="best")
fig.tight_layout()
fig.savefig(FIGURES / "fig_d2_clusters.png", dpi=300)
plt.close(fig)

print(memory.to_string(index=False))
print("\nMedian corr(storage anomaly, SPI-k):\n" + pd.concat([corr, key]).round(2).to_string())
print("\nState changed after h months:\n" + pers.to_string(index=False))
print("\nSilhouette:\n" + sil.to_string(index=False) + f"\nbest k = {best_k}, Ward vs k-means ARI = {ari:.2f}")
print(profile.to_string(index=False))
