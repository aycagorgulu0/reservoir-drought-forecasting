"""Build Deliverable 2 (data selection, preprocessing, transformation and hypotheses) in ACM format.

Every number in the tables is read from reports/deliverable_2/tables/, written by the pipeline
steps 10-31, so the report always matches the code. Run after *python run_pipeline.py --from 10*.
Output: reports/deliverable_2/Deliverable2.docx (convert to PDF with LibreOffice or Word).
"""
import pandas as pd
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

from acm import (COL_W, HERE, SANS, bullets, doc, figure, h1, h2, page_numbers, para, sec, set_columns, table)

T = HERE / "tables"
OUT = HERE / "Deliverable2.docx"
log = pd.read_csv(T / "cleaning_log.csv")
monthly = pd.read_csv(T / "monthly_summary.csv")
rainsum = pd.read_csv(T / "rainfall_summary.csv")
card = pd.read_csv(T / "data_card.csv")
balance = pd.read_csv(T / "class_balance.csv")
transfer = pd.read_csv(T / "transfer_levels.csv")
seas = pd.read_csv(T / "seasonal_share.csv").set_index("name")["median"]
clus = pd.read_csv(T / "reservoir_clusters.csv", index_col=0)
model = pd.read_csv(HERE.parent.parent / "data" / "processed" / "model_table.csv.gz",
                    usecols=["reservoir", "is_system", "split", "month", "si"])
model_si = model.loc[model["si"].isna(), "reservoir"].nunique()


def n(x):
    return f"{int(x):,}"


def rows_of(step):
    return int(log.loc[log["step"].str.startswith(step), "rows_affected"].iloc[0])


def res_of(step):
    return int(log.loc[log["step"].str.startswith(step), "reservoirs_affected"].iloc[0])


final_rows = int(log.loc[log["step"].str.startswith("11"), "rows_after"].iloc[0])
tot = monthly[monthly["basin"] == "all"].iloc[0]
single = model[~model["is_system"]]
split_counts = model["split"].value_counts()

# ---------------------------------------------------------------- title block
set_columns(sec, 1)
page_numbers(sec)
p = para("Forecasting Reservoir Storage and Drought States in the Tajo, Guadiana and Júcar Basins",
         indent=False, size=16, align=WD_ALIGN_PARAGRAPH.CENTER, font=SANS, after=2)
p.runs[0].bold = True
para("Deliverable 2: Data Selection, Preprocessing and Transformation. Minería de Datos, "
     "Universidad de Castilla-La Mancha", indent=False, size=11, align=WD_ALIGN_PARAGRAPH.CENTER, font=SANS, after=10)
authors = doc.add_table(rows=1, cols=3)
authors.alignment = WD_TABLE_ALIGNMENT.CENTER
for j, name in enumerate(["Ayça Görgülü", "Mina Özdoğan", "Beyza Nur Balota"]):
    for i, (txt, sz) in enumerate([(name, 11)]):
        c = authors.cell(i, j)
        c.width = Inches(2.33)
        cp = c.paragraphs[0]
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cp.add_run(txt)
        r.font.size, r.font.name = Pt(sz), SANS

h1("Abstract").paragraph_format.space_before = Pt(12)

# ---------------------------------------------------------------- body
def body():
    b = doc.add_section(WD_SECTION.CONTINUOUS)
    set_columns(b, 2)


ABSTRACT_P = para("", indent=False)
para("**Keywords:** reservoir storage, drought, data integration, preprocessing, SPI, clustering",
     indent=False, before=4, after=4)
body()

h1("1 Introduction")
para("Deliverable 1 defined the problem: forecast the storage of the 114 reservoirs of the Tajo, Guadiana and "
     "Júcar basins, and the official drought and Tajo-Segura transfer states that depend on it, 1 to 6 months "
     "ahead. It set three objectives (**O1** storage regression, **O2** drought-state and transfer-level "
     "classification, **O3** reservoir clustering) and four hypotheses: **H1** hyperannual reservoirs are poorly "
     "predicted by models that look back 12 months or less; **H2** long-memory rainfall features improve "
     "3-6-month forecasts; **H3** forecasting storage and then applying the official rules beats classifying the "
     "state directly; **H4** reservoirs form seasonal and hyperannual groups that need different models.",
     indent=False)
para("This deliverable covers the KDD steps between the raw data and the models: selection and integration of the "
     "sources (Section 2), preprocessing (Section 3), transformation into a modelling table (Section 4) and its data "
     "card (Section 5). Section 6 checks that this data supports the hypotheses, and Section 7 lists the work lines "
     "for the final deliverable. All steps are numbered scripts (*src/10*-*32*) and notebooks (*1.0*, *1.1*) in the "
     "team repository, and every "
     "number in the tables is written by them.")

# ---------------------------------------------------------------- 2 selection and integration
h1("2 Data Selection and Integration")
h2("2.1 Selection")
para(f"From the weekly MITECO reservoir bulletin (BD-Embalses, {n(log.iloc[0]['rows_after'])} rows, 402 "
     f"reservoirs, 1987-2026) we keep the three study basins (Tajo 51, Guadiana 40, Júcar 23 reservoirs) and the "
     f"Duero (35) as a reference, because it is the only Spanish basin in the closest published model [1]. This "
     f"leaves {n(log.iloc[1]['rows_after'])} rows and 149 reservoirs. Two pairs are also modelled as combined systems, "
     "because the rules are defined on their total storage: **Entrepeñas + Buendía** (Tajo-Segura transfer) and "
     "**Alarcón + Contreras** (Júcar drought plan).", indent=False)
h2("2.2 Integration of other sources")
para("Storage shows what happens but not why, so we join four open sources that explain the inflow (Table 1).")
table("Table 1: Integrated sources (all monthly, 1981-2026).", [
    ["Source", "Content", "Use"],
    ["MITECO BD-Embalses [7]", "Weekly storage, capacity", "Target, labels, lags"],
    ["HydroBASINS lev. 8 [5]", "Sub-basin polygons", "Catchment outlines"],
    ["CHIRPS v2.0 [3]", "Rainfall, 0.05° grid", "Rain sums, SPI"],
    ["NOAA CPC", "NAO index", "Large-scale climate"],
    ["NCEP-NCAR SLP [4]", "Sea-level pressure", "WeMO index [6]"],
], [1.3, 1.08, 0.95])
para("**Catchments.** Rainfall must be averaged over the land that drains into each reservoir, not over an "
     "administrative region. Starting from a point inside each reservoir, we collect every HydroBASINS sub-basin "
     "upstream of it. This gives four basin catchments (Tajo 52,126 km², Guadiana 48,748, Júcar district 36,808, "
     "Duero 72,081) and four headwater catchments for the key reservoirs (Entrepeñas 3,946, Buendía 3,459, Alarcón "
     "3,008, Contreras 3,941 km²) (Figure 1). Key reservoirs use their own headwater, each system the mean of its "
     "two headwaters, and the other reservoirs their basin catchment.")
figure("fig_d2_catchments.png", COL_W * 0.95, "Figure 1: Rainfall catchments: basins (light) and headwaters of "
       "the four key reservoirs (dark).")
para("**Rainfall and climate.** CHIRPS combines satellite and gauge data at 0.05° and covers 1981 onwards, so "
     "the 1988 storage series has seven years of rainfall history for the long windows. Mean rainfall is "
     f"{rainsum.loc[rainsum.catchment_id == 'guadiana', 'mean_mm_year'].iloc[0]}-"
     f"{rainsum.loc[rainsum.catchment_id == 'duero', 'mean_mm_year'].iloc[0]} mm/year, and the driest 12-month "
     "periods match the known droughts (1995 Júcar, 2005 Tajo and Guadiana, 2017 Duero). The University of "
     "Barcelona WeMO series was unavailable, so WeMO is computed from reanalysis pressure at San Fernando and Padua "
     "with the published definition [6]. All sources are joined on catchment and month.")

# ---------------------------------------------------------------- 3 preprocessing
h1("3 Preprocessing")
h2("3.1 Cleaning")
para("Table 2 lists every cleaning operation on the weekly series, with the rows it affected. Wrong values are "
     "set to missing and refilled only when the gap is short; flags record both cases, so the models can ignore "
     "imputed or surcharged weeks if needed.", indent=False)
table("Table 2: Cleaning of the weekly series (4 basins).", [
    ["Operation", "Rows", "Res."],
    ["Drop isolated week 6 Oct 1987 (12-week gap)", n(rows_of("2 ")), ""],
    ["Drop placeholders (capacity = 0)", n(rows_of("3 ")), str(res_of("3 "))],
    ["Storage 100-120% of capacity: cap, flag", n(rows_of("5a")), str(res_of("5a"))],
    ["Storage > 120% (up to 7×): set missing", n(rows_of("5b")), str(res_of("5b"))],
    ["Single zero between positives: set missing", n(rows_of("6 ")), str(res_of("6 "))],
    ["One-week spike > 20% of capacity: set missing", n(rows_of("7 ")), str(res_of("7 "))],
    ["Linear interpolation, gaps ≤ 4 weeks, flag", n(rows_of("8 ")), str(res_of("8 "))],
    ["Drop values that could not be filled", n(rows_of("9 ")), ""],
    ["**Clean weekly table**", f"**{n(final_rows)}**", "**149**"],
], [2.35, 0.55, 0.43])
para(f"**Capacity changes.** {res_of('10')} reservoirs report a different capacity at some point. The largest "
     "case is Contreras: 874 hm³ until 2009, 852 until 2019 and 361 since, an operating limit that its storage "
     "never exceeds. Dividing by the reported capacity would turn this into a false jump from 40% to 100% full, so "
     "storage is expressed as a share of the **largest capacity ever reported** (*pct*), and the drought labels "
     "use hm³ directly.")
h2("3.2 Aggregation to months")
para("All other sources and the decisions we predict are monthly, so the weekly readings are aggregated per "
     "reservoir and month into three values, each with a use: the **first** reading (the transfer rules use "
     "storage at the start of the month), the **mean** (the forecasting target, less noisy than one reading) and "
     "the **last** (end-of-month state). Every reservoir gets a complete calendar; gaps of up to two months are "
     f"interpolated and longer ones stay missing. The result has {n(tot['reservoir_months'])} reservoir-months, "
     f"{100 * tot['observed'] / tot['reservoir_months']:.1f}% observed, {int(tot['interpolated'])} interpolated and "
     f"{int(tot['missing'])} missing (three long gaps in small Guadiana and Júcar reservoirs), plus 466 months for "
     "each combined system.", indent=False)

# ---------------------------------------------------------------- 4 transformation
h1("4 Transformation")
para("Steps 30-32 turn the monthly series into one modelling table with one row per reservoir (or system) and "
     "month. Each row contains only what is known at the end of that month; targets come from later months. "
     "The main series is *pct*, the mean monthly storage as % of the largest capacity ever reported. The "
     "features follow the hypotheses:", indent=False)
bullets([
    "**Storage memory (H1):** lags of *pct* at 1-12, 24 and 36 months, changes over 1, 3 and 12 months, rolling "
    "means over 3-36 months, 12-month standard deviation, and the anomaly from the reservoir's usual level for "
    "that calendar month.",
    "**Rainfall memory (H2):** catchment rainfall and its sums over 3-36 months, and SPI [8] at 3-36 months. SPI "
    "standardises accumulated rainfall per calendar month, so dry spells are comparable across catchments.",
    "**Climate:** NAO and WeMO, raw and averaged over 3, 6 and 12 months.",
    "**Season and reservoir:** month as sine and cosine (December next to January), capacity, hydropower flag "
    "and the reservoir's seasonal share (H4).",
])
para("**Feature selection.** Features were chosen by hypothesis rather than by blind search (Table 3). The "
     "exploration (Section 6) then confirmed which windows to keep: rainfall and SPI up to 36 months, because 12 "
     "months is not enough for the hyperannual reservoirs. Selection by importance will be done inside the models "
     "in Deliverable 3, using the validation years only.", indent=False)
para("**Targets and labels.** O1 targets are *pct* 1, 3 and 6 months ahead. For O2, the **State Index** [2] "
     "compares each month's storage (hm³) with the minimum, mean and maximum of that calendar month and is cut at "
     "0.50, 0.30 and 0.15 into Normal, Pre-alert, Alert and Emergency; it is computed for every reservoir and "
     "system. The **transfer level** (1-4) applies the thresholds of RD 638/2021 to Entrepeñas + Buendía storage "
     "at the start of the month. Both labels are also shifted 1, 3 and 6 months ahead as O2 targets. The rules "
     "are coded once (*drought_rules.py*) and will be reused to test H3.")
para("**Preventing leakage.** The split is by time: train up to 2016, validation 2017-2020, test from 2021 "
     f"({n(split_counts.get('train', 0))}, {n(split_counts.get('validation', 0))} and "
     f"{n(split_counts.get('test', 0))} rows). Everything estimated from the data (SPI distributions, WeMO "
     "standardisation, the usual level for each calendar month, the State Index references and the seasonal "
     "share) uses the training years only, so no information from the test period reaches the features.")
table("Table 3: Processing steps and the hypothesis each one serves.", [
    ["Processing step", "Hyp."],
    ["Seasonal share; storage lags up to 12 months", "H1"],
    ["Lags 24-36 m; rainfall sums and SPI 12-36 m; NAO, WeMO", "H2"],
    ["Official labels; storage and state targets 1-6 m ahead", "H3"],
    ["Per-reservoir behaviour features; clustering", "H4"],
], [2.85, 0.48])
bal_rows = [["Series (1988-2026)", "Normal", "Pre-al.", "Alert", "Emerg."]]
for s_ in ["Study reservoirs (114)", "Entrepeñas + Buendía", "Alarcón + Contreras"]:
    b = balance[(balance["group"] == s_) & (balance["split"] == "all")].iloc[0]
    bal_rows.append([s_] + [f"{b[k]:.0f}%" for k in ["Normal", "Pre-alert", "Alert", "Emergency"]])
table("Table 4: Drought-state balance (State Index from storage).", bal_rows, [1.25, 0.52, 0.52, 0.52, 0.52])
tr_ = transfer.iloc[1]
para(f"The classes are usable but unequal, and the test years are wetter than training (Alarcón + Contreras is "
     f"Normal in all test months), so O2 will report macro-F1 and severe-class recall. Since the current rules "
     f"(Oct 2014), the transfer was at level 1, 2, 3 and 4 in {tr_['level_1']}, {tr_['level_2']}, {tr_['level_3']} "
     f"and {tr_['level_4']} of {tr_['months']} months, identical to Deliverable 1.")

# ---------------------------------------------------------------- 5 data card
h1("5 Data Card")
para(f"The modelling table (*data/processed/model_table.csv.gz*) has **{n(len(model))} rows** and "
     f"**{len(card)} columns**: {n(len(single))} reservoir-months of {single['reservoir'].nunique()} reservoirs "
     f"plus {n(model['is_system'].sum())} system-months, from {pd.to_datetime(model['month']).min():%b %Y} to "
     f"{pd.to_datetime(model['month']).max():%b %Y}. Table 5 summarises it by role; the full card (role, source, "
     "unit, type and missing share of every column) is *tables/data_card.csv* in the repository.", indent=False)
groups = [("identifier", "Identifiers", "Basin, role, reservoir, system flag"),
          ("time / bookkeeping", "Time", "Month, year, split, month status"),
          ("static feature", "Static", "Max. capacity, hydropower, seasonal share"),
          ("storage", "Storage", "First and mean storage of the month (hm³)"),
          ("storage feature", "Storage feat.", "pct, lags, changes, rolling stats, anomaly, season"),
          ("rainfall feature", "Rainfall", "CHIRPS rainfall, sums 3-36 m, SPI 3-36"),
          ("climate feature", "Climate", "NAO, WeMO and 3-12 m means"),
          ("label (current month)", "Labels", "State Index, drought state, transfer level"),
          ("target", "Targets", "pct, state and transfer level at t+1, t+3, t+6")]
rows4 = [["Role", "No.", "Content", "Max miss."]]
for key, name, txt in groups:
    c = card[card["role"] == key]
    rows4.append([name, str(len(c)), txt, f"{c['missing_pct'].max():.1f}%"])
table("Table 5: Data card of the modelling table, by column role.", rows4, [0.75, 0.36, 1.72, 0.5], size=7.5)
para(f"Rows per split: train {n(split_counts.get('train', 0))}, validation {n(split_counts.get('validation', 0))}, "
     f"test {n(split_counts.get('test', 0))}. Missing values are structural and are not imputed: long lags are "
     "empty at the start of each series and targets at its end; rainfall is missing only for Oct 2026 (CHIRPS not "
     f"yet released) and WeMO after Feb 2026; the State Index is missing in some months for {model_si} reservoirs "
     "with fewer than 10 training years; the transfer level exists only for Entrepeñas + Buendía (hence 99.3%).")

# ---------------------------------------------------------------- 6 exploration
h1("6 Exploration and Hypotheses")
EDA_START = len(doc.paragraphs)
exec((HERE / "eda_text.py").read_text(encoding="utf-8"))

# ---------------------------------------------------------------- 7 work lines
h1("7 Work Lines")
bullets([
    "**Models (O1, O2):** persistence, climatology and a Baron-style Gradient Boosting baseline with lags up to 12 "
    "months, against the same model with the long-memory features; one model per cluster vs. one global model "
    "(H1, H2, H4). Evaluation on 2021-2026 with NSE, RMSE, macro-F1 and recall of the severe classes.",
    "**H3:** classify the drought state and transfer level directly, and compare with applying *drought_rules.py* "
    "to the forecast storage.",
    "**Clustering (O3):** report forecast skill per cluster, and test whether the operation-based groups or "
    "the seasonal share work better as model inputs.",
    "**Validation of labels and data:** check our transfer levels against the levels declared in the BOE, and "
    "CHIRPS against AEMET gauges; add SAIH inflows if they can be obtained, for the level-1 inflow condition.",
    "**Data:** add SPEI (needs temperature from ERA5 or AEMET), and drop training rows whose target month falls "
    "in the validation period (horizons up to 6 months).",
    "**Tools:** Python (pandas, scikit-learn, LightGBM) and BigML for a second implementation of the models.",
])
para("**Limitations.** The State Index uses storage only (the official one also uses rainfall, river flow and "
     "aquifers); the transfer level ignores the inflow condition; WeMO comes from a coarse 2.5° reanalysis; and "
     "the test years contain few droughts for the two systems.", indent=False, before=3)
para("Code and data: github.com/aycagorgulu0/reservoir-drought-forecasting (tag *v0.2-deliverable2*).",
     indent=False, before=3)

h1("References")
refs = [
    "H. E. Baron et al. 2026. Subseasonal to seasonal prediction and forecasting of reservoir storage using a "
    "machine learning model in the UK, Spain and France. *Int. J. River Basin Management*.",
    "D. Haro-Monteagudo, A. Solera, and J. Andreu. 2017. Drought early warning based on optimal risk forecasts in "
    "regulated river systems: application to the Jucar River Basin. *J. Hydrology* 544, 36-45.",
    "C. Funk et al. 2015. The climate hazards infrared precipitation with stations, a new environmental record for "
    "monitoring extremes. *Scientific Data* 2, 150066.",
    "E. Kalnay et al. 1996. The NCEP/NCAR 40-year reanalysis project. *Bull. Amer. Meteor. Soc.* 77, 437-471.",
    "B. Lehner and G. Grill. 2013. Global river hydrography and network routing: baseline data and new approaches "
    "to study the world's large river systems. *Hydrological Processes* 27, 2171-2186.",
    "J. Martin-Vide and J. A. Lopez-Bustins. 2006. The Western Mediterranean Oscillation and rainfall in the "
    "Iberian Peninsula. *Int. J. Climatology* 26, 1455-1475.",
    "Ministerio para la Transición Ecológica y el Reto Demográfico. 2026. *Base de datos del Boletín Hidrológico "
    "(BD-Embalses)*. Dataset.",
    "T. B. McKee, N. J. Doesken, and J. Kleist. 1993. The relationship of drought frequency and duration to time "
    "scales. *8th Conf. on Applied Climatology*, 179-184.",
    "S. M. Vicente-Serrano and J. I. López-Moreno. 2005. Hydrological response to different time scales of "
    "climatological drought. *Hydrology and Earth System Sciences* 9, 523-533.",
]
for i, r in enumerate(refs, 1):
    p = para(f"[{i}] {r}", indent=False, size=7.5, after=1.5)
    p.paragraph_format.left_indent, p.paragraph_format.first_line_indent = Inches(0.22), Inches(-0.22)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT

from acm import add_runs  # noqa: E402
add_runs(ABSTRACT_P, ABSTRACT_TEXT)
doc.save(OUT)
print("saved", OUT)
