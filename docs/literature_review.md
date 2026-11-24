# Literature review notes

Read in full: papers 1–5 and 9 (PDFs and extracted text in this folder).
Abstract and records only, full text not accessible: papers 6–8 (paywall or bot protection). Paper 10 was read from the abstract page.

---

## 1. Baron, Rickards, Chengot & Keller (2026)
*Subseasonal to seasonal prediction and forecasting of reservoir storage using a machine learning model in the UK, Spain and France.* Int. J. River Basin Management. doi:10.1080/15715124.2026.2729476

- **Data:** 14 UK, **15 Spanish (all in the Duero basin, data from CEDEX)** and 4 French reservoirs. Monthly storage, catchment rainfall and temperature, plus 62 static catchment and reservoir attributes (CAMELS, HydroATLAS, ERA5).
- **Features (97, reduced to 37):** storage lags up to 12 months, weather lags up to 6 months, 3/6/12-month mean rainfall and temperature, month encoded as sine and cosine.
- **Model:** one multi-reservoir model across all reservoirs. Gradient Boosting was chosen over Random Forest, Extra Trees, Bagging and AdaBoost because it overfits less. Tuned settings: 300 trees, max_depth 5.
- **Validation:** a single time-based split (75% of the period for training, about 67% of data points). No cross-validation, because the dataset is small.
- **Results:** median NSE 0.93 one month ahead and 0.80 three months ahead. It beats a SARIMAX benchmark by 0.41–0.48 NSE. The most important features (SHAP) are last month's storage, the average storage for that month, current rainfall, and storage 11 months earlier.
- **Limitations stated by the authors:**
  - Performs poorly on reservoirs **without a clear seasonal signal**: NSE 0.20 for Llyn Brenig.
  - **No operational or human data that changes over time**; only storage itself varies.
  - Underestimates extremes, especially high storage.
  - Can predict storage above 100%.
  - Testing on reservoirs left out of training is preliminary.
  - The authors call for a "wider data set… more regions".
- **Relevance:** this is the closest study to ours. It gives us a ready baseline design to copy, and it **does not cover the Tajo, Guadiana or Júcar basins**.

## 2. García-Feal et al. (2022)
*Comparison of machine learning techniques for reservoir outflow forecasting.* NHESS 22, 3859–3874. doi:10.5194/nhess-22-3859-2022

- **Data:** 8 reservoirs in the Miño-Sil basin, a wet region with 1184 mm of rain a year, mostly used for hydropower. Daily data 2000–2019 from the Confederación Hidrográfica del Miño-Sil, available on request only.
- **Target:** outflow on the next day.
- **Models:** multivariate linear regression, MLP, NARX and LSTM. NARX was best on average and LSTM came second. Every model beat the persistence baseline ("tomorrow equals today").
- **Validation:** chronological split, 70/15/15.
- **Limitations stated by the authors:** only 3 inputs, no operating rules, and results "may not transfer to larger reservoirs or dry climates".
- **Relevance:** a Spanish ML example and good practice (persistence baseline, chronological split). It targets a different variable (outflow) and a different climate and timescale.

## 3. Vicente-Serrano & López-Moreno (2005)
*Hydrological response to different time scales of climatological drought: an evaluation of the SPI in a mountainous Mediterranean basin.* HESS 9, 523–533. doi:10.5194/hess-9-523-2005

- **Data:** Yesa reservoir (Aragón, Ebro basin), monthly storage since 1959, compared with SPI computed over 1–24 months.
- **Result:** storage correlates best with **SPI accumulated over about 8 months (R = 0.59)**; river flow correlates best with about 2 months (R = 0.63). The relationship changes strongly by month.
- **Relevance:** justifies adding rainfall accumulated over 6–12 months (or SPI and SPEI) as model inputs. Baron et al. only go up to 12-month means.

## 4. Torelló-Sentelles & Franzke (2022)
*Drought impact links to meteorological drought indicators and predictability in Spain.* HESS 26, 1821–1844. doi:10.5194/hess-26-1821-2022

- **Data:** 388 drought impact reports (EDII database), 1975–2013, for 6 Spanish regions. Predictors were SPI, SPEI, soil moisture, streamflow, a **standardised reservoir storage index built from MITECO's 322 reservoir stations (our data source)**, and climate patterns (NAO, AO, WeMO, EA, ENSO) accumulated over 1–48 months.
- **Model:** Random Forest classification and regression. Cross-validation used random 10-fold splits, which ignores time order.
- **Results:**
  - Random Forest is skilful: precision of at least 0.97, recall of at least 0.62.
  - Long accumulations of 15–33 months matter most.
  - Climate patterns (WeMO, AO, NAO) are among the top predictors in central regions.
  - Reservoir storage was the top predictor in the south.
- **Relevance:** supports adding the NAO and WeMO climate patterns and long accumulation windows. Their random split is a weakness we can avoid.

## 5. Pellicer-Martínez & Martínez-Paz (2018)
*Climate change effects on the hydrology of the headwaters of the Tagus River: implications for the management of the Tagus–Segura transfer.* HESS 22, 6473–6491. doi:10.5194/hess-22-6473-2018

- **Model:** abcd monthly water-balance model with snowmelt (NSE about 0.80 for inflows to Entrepeñas and Buendía). The transfer was simulated with SIMGES (AQUATOOL) under RD 773/2014.
- **Results:**
  - Average inflow to Entrepeñas and Buendía is 955 hm³/yr today, projected to fall 40% (RCP 4.5) or 47% (RCP 8.5) by 2020–2090.
  - Snow reserves fall 74–80%.
  - The volume transferred falls **70–79%**.
  - Irrigation losses in the Segura basin are about EUR 380–425 M/yr.
- **Limitations stated by the authors:** a scenario tool, not a forecast; demand is fixed; monthly time step; discretionary (non-automatic) transfers are not modelled.
- **Relevance:**
  - Shows how much rides on the transfer level.
  - Shows the level is decided by **storage at the start of the month plus inflow over the last 12 months**.
  - Its transfer thresholds are from the 2014 rules. **The current rules are RD 638/2021** (see the box below).

## 6. Senent-Aparicio et al. (2021), abstract only
*A modelling approach to forecast the effect of climate change on the Tagus–Segura interbasin water transfer.* Water Resources Management 35. doi:10.1007/s11269-021-02919-y

- Inflows to Entrepeñas and Buendía fall 19% (RCP 4.5) or 53% (RCP 8.5) by 2070–2099, so transferable volume could fall by more than 60%.
- Modelling evaporation and the reservoirs' shape (bathymetry) adds about 4% more reduction.

## 7. Lorenzo-Lacruz et al. (2010), abstract only
*The impact of droughts and water management on various hydrological systems in the headwaters of the Tagus River (central Spain).* J. Hydrology 386, 13–26. doi:10.1016/j.jhydrol.2010.01.001

- **Our exact study area.** Drought has dominated since the 1970s. SPEI does slightly better than SPI because temperature matters.
- Entrepeñas and Buendía are **"hyperannual" reservoirs**: they carry water over several years rather than filling and emptying each year.
- After the transfers began (1980s), the link between climate and storage changed because of external demand.

## 8. Lorenzo-Lacruz et al. (2013), abstract only
*Hydrological drought response to meteorological drought in the Iberian Peninsula.* Climate Research 58, 117–131.

- Dam regulation changes and delays how drought shows up in rivers and reservoirs, especially below irrigation reservoirs.

## 9. Jiménez Cando (2025): master's thesis (TFM), UPV
*Predicción estacional de los indicadores de sequía prolongada en la Demarcación Hidrográfica del Júcar.*

- Forecasts the **prolonged-drought index (IES)** for 13 territorial units of the Júcar basin. It uses SPI-12 and **historical analogues plus ECMWF seasonal forecasts**, **not machine learning**, and includes Python tooling.
- **Notes the new drought plan (PES 2024) makes predictive analysis of the indicators a requirement.**
- **Future work it lists:**
  - Measure forecast skill objectively; the thesis did not validate skill.
  - Extend the method to the **scarcity index (IEE)**, which depends on reservoir storage.

## 10. Comparisons of Random Forest and deep learning, abstracts only
- Rao et al. (2026), Ecol. Eng. & Env. Tech. 27(3), 239–252: Random Forest beat a Bi-LSTM on rule-operated California dams (NSE 0.909 vs 0.827 at Shasta).
- Güneş Şen (2025), Sustainability 17(18), doi:10.3390/su17188378: Random Forest and XGBoost reached R² 0.983 on daily dam levels; linear regression reached 0.57.
- **Takeaway:** for reservoirs run by fixed operating rules, tree ensembles are as good as or better than deep learning, which justifies our choice of models.

## 11. Haro-Monteagudo, Solera & Andreu (2017), read in full (accepted manuscript)
*Drought early warning based on optimal risk forecasts in regulated river systems: application to the Jucar River Basin (Spain).* J. Hydrology 544, 36–45. doi:10.1016/j.jhydrol.2016.11.022

- **Problem:** Spain's official drought **State Index (SI)** only describes the current situation by comparing it with history. It has "low, or even non-existent" forecasting ability, so measures are triggered too late.
- **SI formula (CHJ 2007):**
  - If V ≥ the average for that month: SI = ½·(1 + (V − V_avg)/(V_max − V_avg)).
  - Otherwise: SI = ½·(V − V_min)/(V_avg − V_min).
  - V_avg, V_max and V_min are the historical mean, maximum and minimum for that month.
  - The basin SI is a weighted sum over 12 variables (precipitation, streamflow, groundwater levels and reservoir storage). **Reservoir storage makes up about 50% of the Júcar SI.**
- **Scenario thresholds:** Normal SI ≥ 0.5; Pre-alert 0.3–0.5; Alert 0.15–0.3; Emergency < 0.15.
- **Method:**
  - A Monte Carlo optimisation model of the Júcar system, built in AQUATOOL with reservoirs, aquifers and demands.
  - It is driven by 300 synthetic 48-month streamflow series from a multivariate AR(1) model fitted to 1980–2012 data at 16 inflow points.
  - The simulated reservoir storage is converted to SI, which gives the **probability of changing drought scenario 1, 2 and 3 years ahead**.
- **Test period:** 1998–2009, which covers the 1999–2000 drought and the 2005–08 drought (the worst on record).
- **Results:**
  - At 2–3 years ahead, the probability of being worse than "normal" exceeded 50% from June 2004, before the 2005–08 drought.
  - One-year-ahead probabilities rarely signalled change.
  - The risk-based SI lagged the observed SI by **about 6 months** before 2004–08, because the optimisation assumes perfect foresight.
  - **No quantitative skill score is reported.**
- **Context:** **Alarcón and Contreras are operated over several years ("multi-year")**, while Tous is operated annually. This independently confirms our seasonal-share result for these reservoirs.
- **Limitations stated by the authors:**
  - Results depend on the stochastic streamflow model, and AR(1) drifts back to the mean.
  - Optimisation is computationally heavy.
  - Requires a calibrated system model and deep knowledge of the basin, so it is not transferable where that is missing.
  - Needs stakeholder trust.
- **Their warning:** "modelling the past to anticipate future drought is an ineffective and risky approach". Demands and operating rules change over time, and new historical extremes can change the SI scale itself.
- **Relevance to us:**
  1. Gives us an **official drought-state label** we can compute from BD-Embalses for each reservoir (or a group, e.g. Alarcón + Contreras). This makes a classification target with official meaning.
  2. Their method is physics- and optimisation-based and needs a calibrated AQUATOOL model. Ours is **data-driven, cheap and can be applied to many basins**. Their lack of a skill score is a gap we can fill by reporting accuracy measures.
  3. Their warning is a challenge we must answer. We should test on unseen recent periods (the 2022–24 drought, and the period after the 2021 rule change), include changing human factors (transfer volumes) where possible, and compare with a "past analogue" baseline.
  4. A long horizon (1–3 years) matters for multi-year reservoirs, which supports forecasting beyond 3 months.

---

## Our own check: how seasonal are the reservoirs? (from BD-Embalses, monthly data 1988–2026)
"Seasonal share" is the fraction of each reservoir's variation in % full that the average yearly cycle explains. The median per basin (reservoirs with at least 10 years of data):

| Basin | Reservoirs | Median seasonal share |
|---|---|---|
| Duero (the basin Baron et al. used) | 33 | **0.34** |
| Tajo | 51 | 0.15 |
| Guadiana | 36 | 0.07 |
| Júcar | 23 | 0.06 |

Key reservoirs: Entrepeñas 0.04, Buendía 0.07, Alarcón 0.03, Contreras 0.02, La Serena 0.01, Cijara 0.05.
These are mostly **hyperannual** reservoirs: storage swings from one year to the next far more than within a year. Baron et al. report that their model fails on exactly this type of reservoir.

---

## Tajo-Segura transfer rules in force: RD 638/2021, amending RD 773/2014 (BOE)
Rules based on Entrepeñas + Buendía storage at the start of each month:

| Level | Condition | Monthly transfer |
|---|---|---|
| 1 | Storage ≥ 1,300 hm³ **or** 12-month inflow ≥ 1,400 hm³ | 60 hm³ |
| 2 | Storage < 1,300 hm³ and 12-month inflow < 1,400 hm³, but above the level 3 threshold | 27 hm³ |
| 3 | Storage at or below the month's threshold (below) | up to 20 hm³, at the ministry's discretion |
| 4 | Storage < 400 hm³ | 0 |

Level 3 thresholds (hm³):

| Oct | Nov | Dec | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 613 | 609 | 605 | 602 | 597 | 591 | 586 | 645 | 673 | 688 | 661 | 631 |

Annual maximum: 650 hm³ (600 to the Segura, 50 to the Guadiana). Changes in 2021: the level 2 transfer went from 38 to 27 hm³, and the 12-month inflow threshold went from 1,200 to 1,400 hm³.
