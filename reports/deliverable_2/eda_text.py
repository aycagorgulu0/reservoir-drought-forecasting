# Section 6 and abstract of Deliverable 2 (executed by build_report.py, which provides the tables and helpers).
# Numbers come from the tables written by step 33; the interpretation matches those results.
B4 = ["Duero", "Tajo", "Guadiana", "Júcar"]
mem = memory.set_index("basin")
cor = spicorr
key = cor.loc[["Entrepeñas", "Buendía", "Alarcón", "Contreras"]]
key_best = key.max(axis=1)
prof_ = profile.set_index("cluster")
hy, se = prof_.loc[0], prof_.loc[1]
best_sil = sil["silhouette"].max()
st = persist.pivot(index="series", columns="horizon", values="changed")


def pc(x):
    return f"{100 * x:.0f}%"


para("All checks use the training years only (1988-2016) and reservoirs with at least 10 years of data "
     "(step *33_explore.py*).", indent=False)
h2("6.1 Memory of storage and rainfall (H1, H2)")
para(f"The **seasonal share** confirms Deliverable 1 on the cleaned data: the yearly cycle explains "
     f"{mem.loc['Duero', 'seasonal_share']:.2f} of the storage variance in the Duero but only "
     f"{mem.loc['Tajo', 'seasonal_share']:.2f}, {mem.loc['Guadiana', 'seasonal_share']:.2f} and "
     f"{mem.loc['Júcar', 'seasonal_share']:.2f} in the Tajo, Guadiana and Júcar (Table 5). To measure memory we "
     "use the storage **anomaly** (storage minus the usual level for that calendar month), so the yearly cycle "
     f"does not count as memory. In the Duero and Tajo the anomaly fades within a year (autocorrelation "
     f"{mem.loc['Duero', 'acf_12']:.2f} and {mem.loc['Tajo', 'acf_12']:.2f} at 12 months); in the Guadiana and "
     f"Júcar it persists ({mem.loc['Guadiana', 'acf_12']:.2f} and {mem.loc['Júcar', 'acf_12']:.2f}).", indent=False)
table("Table 5: Behaviour per basin (median over reservoirs). ACF: autocorrelation of the storage anomaly; "
      "best SPI: window most correlated with it.", [
          ["Basin", "Res.", "Seas. share", "ACF 12m", "ACF 24m", "Best SPI", "Best ≥24m"]] +
      [[b, str(int(mem.loc[b, "reservoirs"])), f"{mem.loc[b, 'seasonal_share']:.2f}", f"{mem.loc[b, 'acf_12']:.2f}",
        f"{mem.loc[b, 'acf_24']:.2f}", f"{int(mem.loc[b, 'best_spi_median'])} m", pc(mem.loc[b, 'share_best_24_36'])]
       for b in B4], [0.62, 0.33, 0.5, 0.45, 0.45, 0.48, 0.5], size=7)
para("Rainfall tells the same story (Figure 2). The anomaly of Duero and Tajo reservoirs follows SPI-12 best, "
     "close to the 8 months found for seasonal reservoirs [9]. In the Guadiana and Júcar the correlation keeps "
     f"rising to 24-36 months, which is the best window for {pc(mem.loc['Guadiana', 'share_best_24_36'])} and "
     f"{pc(mem.loc['Júcar', 'share_best_24_36'])} of their reservoirs. The four **key reservoirs** all respond "
     f"best to 24 or 36 months (r = {key_best.min():.2f}-{key_best.max():.2f}), against "
     f"{key['corr_spi_3'].min():.2f}-{key['corr_spi_3'].max():.2f} at 3 months; the Tajo median hides this "
     "because most of its reservoirs are small and seasonal. This supports **H1** and **H2**: a model that looks "
     "back 12 months or less misses much of the signal exactly where the transfer and drought decisions are "
     "made, so the 24- and 36-month lags and SPI belong in the feature set.")
figure("fig_d2_spi_correlation.png", COL_W, "Figure 2: Median correlation between the storage anomaly and SPI "
       "over 3-36 months, per basin (number of reservoirs).")
h2("6.2 Groups of reservoirs (H4)")
para("As a first test of O3 we describe each reservoir by five standardised features (seasonal share, amplitude "
     "of the yearly cycle, year-to-year variability and anomaly autocorrelation at 12 and 24 months) and apply "
     f"k-means for k = 2-6 ({int(hy['reservoirs'] + se['reservoirs'])} reservoirs with all features). The silhouette is highest for **k = {best_k}** ({best_sil:.2f}). One group "
     f"({int(hy['reservoirs'])} reservoirs, median seasonal share {hy['seasonal_share']:.2f}) is hyperannual and "
     f"holds {int(hy['júcar'])} of the {int(hy['júcar'] + se['júcar'])} Júcar and {int(hy['guadiana'])} of the "
     f"{int(hy['guadiana'] + se['guadiana'])} Guadiana reservoirs and all four key reservoirs; the other "
     f"({int(se['reservoirs'])}, share {se['seasonal_share']:.2f}) is seasonal and holds {int(se['duero'])} of the "
     f"{int(hy['duero'] + se['duero'])} Duero reservoirs (Figure 3). This supports **H4**, but the separation is "
     f"weak and Ward clustering agrees only partly (adjusted Rand index {ari:.2f}): reservoirs form a continuum "
     "rather than two clean classes. The final deliverable will therefore test the groups and the seasonal share "
     "as model inputs, not only as fixed partitions.", indent=False)
figure("fig_d2_clusters.png", COL_W, "Figure 3: Reservoirs by seasonal share and 24-month anomaly "
       "autocorrelation; colour = k-means group, marker = basin.")
h2("6.3 Is the state worth forecasting? (H3)")
para(f"If the labels rarely changed, copying the current state would be enough. In the study reservoirs the "
     f"drought state changes within 1, 3 and 6 months in {pc(st.loc['Study reservoirs', 1])}, "
     f"{pc(st.loc['Study reservoirs', 3])} and {pc(st.loc['Study reservoirs', 6])} of the months, and the transfer "
     f"level in {pc(st.loc['Transfer level', 1])}, {pc(st.loc['Transfer level', 3])} and "
     f"{pc(st.loc['Transfer level', 6])}. Persistence is therefore a strong baseline at 1 month but a weak one at "
     "6, which is the horizon where a forecast is useful. H3 will compare classifying the state directly with "
     "applying *drought_rules.py* to the forecast storage, against this persistence baseline.", indent=False)

ABSTRACT_TEXT = (
    "This deliverable prepares the data for forecasting reservoir storage and the official drought and Tajo-Segura "
    "transfer states in the Tajo, Guadiana and Júcar basins. We integrate the weekly MITECO reservoir bulletin with "
    "CHIRPS rainfall over catchments built from HydroBASINS, SPI and the NAO and WeMO climate indices. Cleaning, "
    f"logged step by step, yields {n(final_rows)} weekly rows for 149 reservoirs, aggregated to "
    f"{n(tot['reservoir_months'])} reservoir-months. The modelling table ({n(len(model))} rows, {len(card)} "
    "columns, documented in a data card) holds storage and rainfall memory features, the official labels and "
    "1-6-month targets, with a time split and no information from the test years. A first exploration supports "
    "the hypotheses: storage in the Guadiana and Júcar and in the four key reservoirs follows rainfall accumulated "
    "over 24-36 months rather than 12, reservoirs split into hyperannual and seasonal groups, and the drought state "
    f"changes within 6 months in {pc(st.loc['Study reservoirs', 6])} of cases.")
