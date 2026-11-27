# Section 6 and abstract of Deliverable 2 (executed by build_report.py, which provides the tables and helpers).
# The numbers are recomputed here with the same code as notebooks 1.0 (Mina) and 1.1 (Beyza), so they match them.
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler
from scipy.cluster.hierarchy import fcluster, linkage

full = pd.read_csv(HERE.parent.parent / "data" / "processed" / "model_table.csv.gz", parse_dates=["month"])
train = full[full["split"] == "train"]
SPI = ["spi_3", "spi_6", "spi_12", "spi_24", "spi_36"]

# notebook 1.0, figure 1: pct vs SPI-k, systems and study reservoirs pooled per basin
corr = {}
for name, g in train[train["is_system"]].groupby("reservoir"):
    corr[name] = g[["pct"] + SPI].corr()["pct"][SPI]
st = train[(train["role"] == "study") & ~train["is_system"]]
for b in ["Tajo", "Guadiana", "Júcar"]:
    corr[f"{b} (pooled)"] = st[st["basin"] == b][["pct"] + SPI].corr()["pct"][SPI]
corr = pd.DataFrame(corr).T
assert abs(corr.loc["Entrepeñas + Buendía", "spi_24"] - 0.464) < 0.001  # same as notebook 1.0

# notebook 1.0, figure 5: winter (Oct-Mar) rainfall vs NAO / WeMO per basin
w = train[train["month"].dt.month.isin([10, 11, 12, 1, 2, 3])].dropna(subset=["precip_mm", "nao", "wemo"])
nao = w.groupby("basin").apply(lambda g: g["precip_mm"].corr(g["nao"]))
wemo = w.groupby("basin").apply(lambda g: g["precip_mm"].corr(g["wemo"]))

# notebook 1.0, figure 4: class balance per split (study reservoirs)
cb = balance[balance["group"] == "Study reservoirs (114)"].set_index("split")

# notebook 1.1: clustering
FEATS = ["seasonal_share", "mean_pct", "std_pct", "lag12_autocorr", "corr_spi12", "corr_spi36", "log_capacity"]
X = StandardScaler().fit_transform(clus[FEATS])
sil = {k: silhouette_score(X, KMeans(n_clusters=k, n_init=20, random_state=0).fit_predict(X)) for k in range(2, 7)}
best_k = max(sil, key=sil.get)
ari_ward = adjusted_rand_score(clus["cluster"], fcluster(linkage(X, "ward"), best_k, "maxclust"))
size = clus["cluster"].value_counts().sort_index()
med = clus.groupby("cluster")[FEATS].median()
hydro = full.drop_duplicates("reservoir").set_index("reservoir")["hydro_flag"]
hyd = clus.join(hydro).groupby("cluster")["hydro_flag"].mean()
BIGML = HERE / "bigml" / "bigml_clusters.csv"


def pc(x):
    return f"{int(x + 0.5)}%"  # round half up, as in the notebooks


para("The exploration is in two notebooks that use the training years only: *1.0-eda-storage-and-rainfall* "
     "(rainfall memory, seasonal share, the Entrepeñas + Buendía timeline, class balance and climate indices) and "
     "*1.1-reservoir-clustering* (reservoir groups, also built in BigML).", indent=False)
h2("6.1 Memory of storage and rainfall (H1, H2)")
para(f"The **seasonal share** confirms Deliverable 1 on the cleaned data: the median is {seas['Duero']:.2f} in the "
     f"Duero but {seas['Tajo']:.2f}, {seas['Guadiana']:.2f} and {seas['Júcar']:.2f} in the Tajo, Guadiana and Júcar, "
     f"and only {seas['Entrepeñas']:.2f} and {seas['Alarcón']:.2f} for Entrepeñas and Alarcón. Our reservoirs change "
     "more between years than within a year, unlike the Duero reservoirs modelled by Baron et al. [1].", indent=False)
rows = [["Series / SPI window", "3 m", "6 m", "12 m", "24 m", "36 m"]]
for name in ["Entrepeñas + Buendía", "Alarcón + Contreras", "Tajo (pooled)", "Guadiana (pooled)", "Júcar (pooled)"]:
    r = corr.loc[name]
    best = r.idxmax()
    rows.append([name] + [f"**{v:.2f}**" if k == best else f"{v:.2f}" for k, v in r.items()])
table("Table 6: Correlation of storage (% full) with SPI, training years; best window in bold.", rows,
      [1.25, 0.42, 0.42, 0.42, 0.42, 0.4], size=7)
eb, ac = corr.loc["Entrepeñas + Buendía"], corr.loc["Alarcón + Contreras"]
para(f"**Rainfall memory** (Table 6, Figure 2). Storage of the two systems follows rainfall accumulated over 24-36 "
     f"months (r = {eb['spi_24']:.2f} at SPI-24 for Entrepeñas + Buendía, {ac['spi_36']:.2f} at SPI-36 for Alarcón + "
     f"Contreras) and hardly 3-month rainfall (r ≈ {eb['spi_3']:.2f}). Pooled Guadiana and Júcar reservoirs also peak "
     "at 24 months, while the Tajo peaks at 12, close to the 8 months found for seasonal reservoirs [9]. The "
     "Entrepeñas + Buendía timeline shows the same: the 1995 and 2005 storage lows follow long negative SPI-24 "
     "periods. This supports **H1** and **H2**: a model that looks back 12 months or less misses much of the signal "
     "exactly where the transfer and drought decisions are made, so 24- and 36-month lags and SPI stay in the "
     "feature set.")
figure("fig_d2_spi_correlation.png", COL_W, "Figure 2: Correlation of storage with SPI over 3-36 months for the "
       "two systems and the study basins (notebook 1.0).")
para(f"**Climate indices.** Winter (Oct-Mar) rainfall correlates negatively with the NAO "
     f"({nao[['Duero', 'Tajo', 'Guadiana', 'Júcar']].max():.2f} to {nao[['Duero', 'Tajo', 'Guadiana', 'Júcar']].min():.2f}) "
     f"and the WeMO ({wemo['Duero']:.2f} in the Duero to {wemo['Guadiana']:.2f} in the Guadiana). The Júcar is the "
     f"only basin where the WeMO ({wemo['Júcar']:.2f}) is stronger than the NAO ({nao['Júcar']:.2f}), as expected near "
     "the Mediterranean [6]. These are same-season links, so Deliverable 3 will test whether their lagged means add "
     "forecast skill.")

h2("6.2 Groups of reservoirs (H4)")
txt = (f"Notebook 1.1 describes the {len(clus)} study reservoirs with enough training data by seven standardised "
       "features (seasonal share, mean and standard deviation of storage, 12-month autocorrelation, correlation "
       f"with SPI-12 and SPI-36, log capacity). k-means is best at **k = {best_k}** (silhouette {sil[best_k]:.2f}), "
       f"and Ward clustering gives almost the same split (adjusted Rand index {ari_ward:.2f}). The groups are not "
       "seasonal vs. hyperannual (both have a median seasonal share of about 0.1) but differ in **operation**: "
       f"cluster 0 ({size[0]} reservoirs, including all four key reservoirs) empties and refills with rainfall "
       f"(correlation with SPI-36 {med.loc[0, 'corr_spi36']:.2f}, standard deviation {med.loc[0, 'std_pct']:.0f} "
       f"points), while cluster 1 ({size[1]}) is kept almost full whatever the rain (median "
       f"{med.loc[1, 'mean_pct']:.0f}% full, correlation {med.loc[1, 'corr_spi36']:.2f}); {pc(100 * hyd[1])} of "
       f"cluster 1 are hydropower dams on the main rivers, against {pc(100 * hyd[0])} of cluster 0 (Figure 3).")
txt += (" The same table clustered in **BigML** (K-means, k = 2) puts 101 of the 108 reservoirs (94%) in the same "
        "group (adjusted Rand index 0.75); all 28 reservoirs of cluster 1 match, and the 7 differences lie near the "
        "boundary. BigML first read the file with a Turkish browser locale, turning 0.1266 into 1266; setting the "
        "source locale to English fixed it, a reminder to check tool settings before comparing results.")
para(txt, indent=False)
para("This partly supports **H4**: the reservoirs need different treatment, but the split is by operation rather "
     "than seasonality, and the seasonal-vs-hyperannual contrast is between our basins and the Duero. For cluster 1 "
     "rainfall features will add little, so Deliverable 3 will report skill per cluster.")
figure("fig_d2_cluster_profiles.png", COL_W * 0.95, "Figure 3: Study reservoirs by seasonal share and correlation "
       "with SPI-36, coloured by k-means cluster; marker size = capacity (notebook 1.1).")

h2("6.3 Labels over time (H3)")
para(f"The class balance of the study reservoirs shifts between periods: the test years are the wettest "
     f"({cb.loc['test', 'Normal']:.0f}% Normal, {cb.loc['test', 'Emergency']:.0f}% Emergency), while the validation "
     f"years, which include the 2017-18 drought, have more Pre-alert ({cb.loc['validation', 'Pre-alert']:.0f}%) and "
     f"Alert ({cb.loc['validation', 'Alert']:.0f}%) months. For the two systems the test period has no Alert or "
     "Emergency month at all. H3 will therefore be tested on all 114 study reservoirs, with macro-F1 and recall of "
     "the severe classes, comparing direct classification with applying *drought_rules.py* to the forecast "
     "storage.", indent=False)

ABSTRACT_TEXT = (
    "This deliverable prepares the data for forecasting reservoir storage and the official drought and Tajo-Segura "
    "transfer states in the Tajo, Guadiana and Júcar basins. We integrate the weekly MITECO reservoir bulletin with "
    "CHIRPS rainfall over catchments built from HydroBASINS, SPI and the NAO and WeMO climate indices. Cleaning, "
    f"logged step by step, yields {n(final_rows)} weekly rows for 149 reservoirs, aggregated to "
    f"{n(tot['reservoir_months'])} reservoir-months. The modelling table ({n(len(model))} rows, {len(card)} "
    "columns, documented in a data card) holds storage and rainfall memory features, the official labels and "
    "1-6-month targets, with a time split and no information from the test years. The exploration supports the "
    "hypotheses: the key reservoirs follow rainfall accumulated over 24-36 months rather than 12, and the study "
    "reservoirs split into two groups, regulating reservoirs driven by rainfall and reservoirs kept full for "
    "hydropower, that will need different models.")
