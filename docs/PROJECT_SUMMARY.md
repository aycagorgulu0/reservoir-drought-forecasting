# Data Mining Project: Summary of Work So Far

**Course:** Minería de Datos, Universidad de Castilla-La Mancha (UCLM)
**Team:** Ayça Görgülü, Mina Özdoğan, Beyza Nur Balota
**Project title:** *Forecasting Reservoir Storage and Drought States in the Tajo, Guadiana and Júcar Basins*
**Status:** Deliverable 1 (Problem Definition) finished on 30 October 2026. Deliverable 2 is due **27 November 2026**.

---

## 1. The assignment

The course project is a group KDD project (slides `DM2026_S00_KICKOFF.pdf`) with three deliverables:

| Deliverable | Weight | Format | Due | Contents |
|---|---|---|---|---|
| **E01.1 Problem definition** | 7.5% | ACM, 1-5 pages | 30 Oct | Data source, brief data description, hypothesis and objectives, brief feasibility study |
| **E01.2 Data exploration** | 15% | ACM, 2-8 pages | 27 Nov | Selected parts of Deliverable 1, data and feature selection, preprocessing, transformation; interview with the professors |
| **E01.3 Modelling and results** | 27.5% | ACM, 4-10 pages | 16 Dec | Introduction, KDD phases carried out, results, conclusions and future work; presentation in class |

Other graded parts: theoretical work on KDD (15%), GitHub repository (25%), interviews and presentation (10%).
Grading criteria include originality and complexity of the data, preprocessing and mining techniques, quality of explanations, **variety of tools used**, and **punctuality**.

The Moodle brief for Deliverable 1 also asked for related work ("antecedentes") and data enrichment sources.

---

## 2. Topic chosen

**Forecasting reservoir storage and drought states** in the Tajo, Guadiana and Júcar river basins. These rivers start in Castilla-La Mancha, and their reservoirs control two major water decisions:

- **Entrepeñas + Buendía** (Guadalajara/Cuenca) feed the **Tajo-Segura transfer** to Murcia and Alicante. The amount transferred each month is set by law according to how much water these two reservoirs hold.
- **Alarcón + Contreras** (Cuenca) regulate the Júcar, which supplies Valencia and Albacete.

The official drought indicators in Spain only describe the **current** situation. The project uses data mining to **predict** storage and the official states months ahead.

### Scope decisions
- **Study area:** the three **complete** basins (114 reservoirs). They also extend into Madrid, Castilla y León, Extremadura, Andalucía, Aragón and the Valencia region, so the project is **not** limited to Castilla-La Mancha. An earlier title suggested it was; this was corrected.
- **Key reservoirs:** Entrepeñas, Buendía, Alarcón and Contreras (all in Castilla-La Mancha).
- **Reference basin:** the Duero (35 reservoirs), used only for comparison because it is the Spanish basin studied by the closest published paper.
- Three basins were judged enough: about 50,000 reservoir-months, more than three times the data of the closest study, and a full semester of work.

---

## 3. The data

### Main dataset
**MITECO, Base de datos del Boletín Hidrológico (BD-Embalses)**: the weekly reservoir bulletin of the Spanish Ministry for the Ecological Transition. Downloaded as `BD-Embalses.mdb` (Microsoft Access, 213 MB), one table: `T_Datos Embalses 1988-2026`.

| Original field | English name | Meaning |
|---|---|---|
| AMBITO_NOMBRE | basin | River basin district (16) |
| EMBALSE_NOMBRE | reservoir | Reservoir name (402) |
| FECHA | date | Weekly measurement date |
| AGUA_TOTAL | capacity_hm3 | Total capacity (hm³) |
| AGUA_ACTUAL | stored_hm3 | Water stored (hm³) |
| ELECTRICO_FLAG | hydro_flag | 1 if used for hydropower |
| (derived) | pct_full | stored / capacity × 100 |

Numbers were stored as text in Spanish format ("1.234,56") and had to be converted.

### Size

| Measure | Value |
|---|---|
| Records | 724,217 weekly rows |
| Period | 6 Oct 1987 to 27 Oct 2026 (2,028 weeks) |
| Basins / reservoirs | 16 / 402 (285 reporting in 1988, 375 in 2026) |
| Total capacity | 56,049 hm³ (56.8% full in the latest week) |
| Study area (Tajo, Guadiana, Júcar) | 114 reservoirs, 217,717 rows, 23,440 hm³ (42% of Spain) |

| Key reservoir | Basin | Capacity | Lowest % | Highest % |
|---|---|---|---|---|
| Entrepeñas | Tajo | 886 hm³ | 6.0% | 86.8% |
| Buendía | Tajo | 1,705 hm³ | 4.2% | 59.7% |
| Alarcón | Júcar | 1,118 hm³ | 2.5% | 81.3% |
| Contreras | Júcar | 874 hm³ | 1.7% | 93.6% |

Entrepeñas + Buendía together ranged from **124 hm³ (October 1995)** to **1,682 hm³ (March 2026)**.

### Data quality issues found
| Issue | Rows | Reservoirs | Planned action |
|---|---|---|---|
| Capacity and storage = 0 (reservoir not yet in the bulletin, mostly before 1999) | 18,867 | 71 | Remove |
| Storage above capacity (flood surcharge or changed capacity) | 1,264 | 90 | Cap at 100% or flag |
| Missing values | 2 | | Interpolate |

The cleaned CSV still contains all original rows; the placeholder rows are only removed in the plotting scripts.

---

## 4. Key findings so far

### 4.1 Our reservoirs are "hyperannual"
We measured the **seasonal share**: how much of each reservoir's variation is explained by its average yearly cycle.

| Basin / reservoir | Seasonal share (median) |
|---|---|
| Duero (reference) | **0.34** |
| Tajo | 0.15 |
| Guadiana | 0.07 |
| Júcar | 0.06 |
| Entrepeñas / Buendía | 0.04 / 0.07 |
| Alarcón / Contreras | 0.03 / 0.02 |

Our reservoirs change much more **between years** than **within a year**. This matters because the best published model (Baron et al. 2026) **fails on exactly this kind of reservoir**. This is the main originality argument of the project. Haro-Monteagudo et al. (2017) independently confirm that Alarcón and Contreras are operated over several years.

### 4.2 The Tajo-Segura transfer is often in a critical state
Applying the official rules to storage since October 2014 (145 months): level 1 in 15 months, level 2 in 55, level 3 in 58, level 4 in 17. The system was in the "exceptional" levels 3 or 4 in **52% of months**.

### 4.3 Drought states are reasonably balanced
Using the official State Index formula on Alarcón + Contreras storage (466 months): Normal 49%, Pre-alert 23%, Alert 13%, Emergency 15%. This gives a usable classification target.

### 4.4 Official transfer rules (RD 638/2021, amending RD 773/2014)
Based on Entrepeñas + Buendía storage at the start of each month:

| Level | Condition | Monthly transfer |
|---|---|---|
| 1 | Storage ≥ 1,300 hm³ **or** 12-month inflow ≥ 1,400 hm³ | 60 hm³ |
| 2 | Below level 1, above the level 3 threshold | 27 hm³ |
| 3 | Storage at or below the monthly threshold (586-688 hm³) | up to 20 hm³ (discretionary) |
| 4 | Storage < 400 hm³ | 0 |

Level 3 thresholds (hm³): Oct 613, Nov 609, Dec 605, Jan 602, Feb 597, Mar 591, Apr 586, May 645, Jun 673, Jul 688, Aug 661, Sep 631. The annual maximum is 650 hm³. The 2021 change cut the level 2 volume (38 to 27 hm³) and raised the inflow threshold (1,200 to 1,400 hm³).

**Caution:** our labels are approximations. The transfer level ignores the 12-month inflow condition (no inflow data yet), and our State Index uses storage only (the official one also uses rainfall, river flow and groundwater).

---

## 5. Literature review

Full notes: `docs/literature_review.md`. The paper PDFs and their extracted text are kept outside the repository (copyright), in `project/literature_pdfs/`.

| Study | What it does | What we take from it |
|---|---|---|
| **Baron et al. 2026** (Int. J. River Basin Management) | Gradient Boosting, 33 reservoirs (UK, Spain, France), monthly storage 1 and 3 months ahead, median NSE 0.93 / 0.80 | Closest work and baseline design. **All Spanish reservoirs are in the Duero; fails on reservoirs without a seasonal signal; no operations data** |
| García-Feal et al. 2022 (NHESS) | ANNs vs linear regression, next-day outflow, Miño-Sil | Persistence baseline, time-based split; may not work in dry climates |
| Rao et al. 2026; Güneş Şen 2025 | Random Forest / XGBoost vs deep learning for dams | Tree ensembles suit rule-operated reservoirs |
| Vicente-Serrano & López-Moreno 2005 (HESS) | SPI time scales vs storage | Storage responds to about 8 months of accumulated rainfall |
| Lorenzo-Lacruz et al. 2010 (J. Hydrology) | Drought and management in the Tajo headwaters | SPEI and water management matter |
| Torelló-Sentelles & Franzke 2022 (HESS) | Random Forest for drought impacts in Spain | Use long windows (15-33 months) and NAO/WeMO; avoid random CV |
| **Haro-Monteagudo et al. 2017** (J. Hydrology) | Optimisation-based drought early warning, Júcar | Official State Index formula and thresholds; no accuracy score; warns that "modelling the past" is risky |
| Jiménez Cando 2025 (UPV master's thesis) | Analogue + ECMWF forecasts of a Júcar drought index | New drought plans require forecasts; no ML, no skill evaluation |
| Pellicer-Martínez & Martínez-Paz 2018; Senent-Aparicio et al. 2021 | Climate change impact on the transfer | Transferable water could fall 60-79% this century; long-term scenarios only |

Read in full: Baron, García-Feal, Vicente-Serrano, Torelló-Sentelles, Pellicer-Martínez, Haro-Monteagudo, Jiménez Cando, and the BOE decree. Only abstracts were available for Senent-Aparicio, Lorenzo-Lacruz, Rao and Güneş Şen.

**Gap:** to our knowledge, no study uses data mining to forecast storage and the official drought and transfer states in these semi-arid, hyperannual reservoirs.

---

## 6. Project design (from Deliverable 1)

**Problem:** given a reservoir's storage history and recent climate, can we predict its storage and its official drought or transfer state several months ahead?

**Objectives** (covers all three main data-mining tasks):
- **O1, regression:** forecast monthly % full 1, 3 and 6 months ahead, adding long-memory features (rainfall and SPI/SPEI over 12-36 months, NAO, WeMO) to a Baron-style Gradient Boosting baseline.
- **O2, classification:** predict the drought state (Normal / Pre-alert / Alert / Emergency) and the transfer level (1-4).
- **O3, clustering:** group the 114 reservoirs by behaviour (seasonal vs hyperannual) with k-means or hierarchical clustering.

**Hypotheses:**
- **H1:** hyperannual reservoirs are poorly predicted by models that look back 12 months or less.
- **H2:** long-memory features improve 3-6-month forecasts for them.
- **H3:** forecasting storage and then applying the official rules beats classifying the state directly.
- **H4:** reservoirs form distinct groups that need different models.

**Evaluation plan:** time-based split (train 1988-2016, validate 2017-2020, test 2021-2026); baselines are persistence, monthly climatology, historical analogues and the Baron feature set; metrics are NSE, RMSE and bias for storage, macro-F1 and severe-class recall for states, and silhouette for clusters.

**Enrichment sources planned:** AEMET OpenData (rainfall, temperature; free API key), Copernicus ERA5 (gridded climate, snow), SAIH Tajo / CEDEX (inflows, needed for transfer level 1), MITECO drought reports (official indices), BOE transfer orders (declared levels), NOAA NAO and University of Barcelona WeMO indices, INE / ESYRCE / Red Eléctrica (demand proxies).

---

## 7. Deliverable 1: how it was produced

1. First version: an 11-page single-column Word report (`Deliverable1_Problem_Definition.docx/.pdf`), later edited by the team (UCLM logo, title-case headings, date 29 October).
2. Requested changes applied: all text black, no long dashes, title corrected to the real scope.
3. The kickoff slides showed the deliverable must be **ACM format, 1-5 pages, with a feasibility study**. The report was rewritten:
   - A LaTeX version for Overleaf was prepared first but not used (deleted on 24 Nov).
   - The final version is an **ACM-style two-column Word document**, **3 pages**, with abstract, keywords, a new **Feasibility Study** section (data, technical needs, risks table, timeline) and 13 references.
4. **Final files:** `Deliverable1_ACM.docx` and `Deliverable1.pdf` (3 pages).

---

## 8. Repository layout

The code is organized as the GitHub repository `reservoir-drought-forecasting/` (see its `README.md`).

| Folder | Contents |
|---|---|
| `data/raw/` | `BD-Embalses.mdb`, the original MITECO database (not in git, 213 MB) |
| `data/interim/` | `reservoirs_spain_weekly.csv`: clean CSV, English columns, numeric values, `pct_full` (not in git, 37 MB) |
| `data/processed/` | Final modelling tables (Deliverable 2) |
| `src/` | Pipeline scripts, numbered in run order; `paths.py` holds all shared paths |
| `figures/` | All figures |
| `reports/deliverable_1/` | `Deliverable1.pdf` (final, 3 pages) and the scripts that generated its drafts |
| `reports/deliverable_2/` | Deliverable 2 report |
| `docs/` | This summary and `literature_review.md` |

### Scripts (`src/`)
| Script | What it does |
|---|---|
| `00_inspect_mdb.py` | Lists tables, columns and sample rows of the .mdb |
| `01_convert_to_csv.py` | Converts the .mdb to the clean CSV |
| `02_basic_stats.py` | Prints dataset statistics (size, missing values, per-basin totals, key reservoirs) |
| `03_make_plots.py` | Creates the five exploratory figures |
| `04_make_acm_figures.py` | Creates the two column-sized figures used in the ACM report |

The report builders in `reports/deliverable_1/` (`build_acm_docx.py`, `build_long_report.py`) now write `*_generated.docx` files, so they never overwrite the hand-edited Word versions. The hand-edited `Deliverable1_ACM.docx` stays in `project/deliverable_1/`, outside the repository.

Requirements: Python 3.11 with pandas, numpy, matplotlib, pyodbc (and the Microsoft Access ODBC driver), python-docx (`requirements.txt`).

### Figures (`figures/`)
| File | Shows |
|---|---|
| `fig1_entrepenas_buendia.png` | Combined Entrepeñas + Buendía storage 1988-2026 |
| `fig2_basins_pct_full.png` | Monthly % full of the three basins |
| `fig3_seasonal_pattern.png` | Typical yearly cycle per basin |
| `fig4_annual_heatmap.png` | Annual mean storage per basin (drought years stand out) |
| `fig5_coverage.png` | Number of reservoirs reporting per year |
| `acm_fig1_entrepenas_buendia.png`, `acm_fig2_seasonal.png` | Column-sized versions for the ACM report |

---

## 9. Next steps: Deliverable 2 (due 27 November)

Deliverable 2 covers **data selection, preprocessing and transformation** (ACM format, 2-8 pages), plus an interview with the professors.

1. **Cleaning:** remove the 18,867 placeholder rows, cap or flag storage above capacity, interpolate the 2 missing values.
2. **Aggregation:** weekly to monthly storage per reservoir; build combined series for Entrepeñas + Buendía and Alarcón + Contreras.
3. **Enrichment:**
   - Register for an AEMET OpenData API key and a Copernicus account (ERA5); download rainfall and temperature for the catchments.
   - Download NAO (NOAA) and WeMO indices.
   - Look for inflow data (SAIH Tajo, CEDEX) for the transfer level 1 condition.
   - Collect the declared transfer levels from the BOE orders to validate our labels.
4. **Transformation and features:** storage lags (1-12 months), rainfall accumulated over 3-36 months, SPI/SPEI, month as sine/cosine, seasonal share per reservoir.
5. **Labels:** compute the State Index drought state and the transfer level for every month.
6. **Exploration:** correlations between accumulated rainfall and storage (check the ~8-month lag), class balance, first clustering of reservoirs.
7. **GitHub repository** (25% of the grade): structure done (`reservoir-drought-forecasting/`); push to the team GitHub account and keep adding Deliverable 2 scripts to `src/`.
8. **Tools:** try BigML (course tool) alongside Python, since variety of tools is graded.
