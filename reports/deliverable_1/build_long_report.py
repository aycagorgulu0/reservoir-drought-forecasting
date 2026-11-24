"""Build Deliverable 1 (problem definition report) as a Word document."""
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).parent
FIG = HERE.parent.parent / "figures"
# Early 11-page draft of Deliverable 1, kept for reference (not the submitted version).
OUT = HERE / "Deliverable1_long_draft_generated.docx"

ACCENT = RGBColor(0x00, 0x00, 0x00)
INK2 = RGBColor(0x00, 0x00, 0x00)
HEADER_FILL = "D9D9D9"

doc = Document()

# -- base styles --
sec = doc.sections[0]
sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
for side in ("left_margin", "right_margin"):
    setattr(sec, side, Cm(2.3))
sec.top_margin, sec.bottom_margin = Cm(2.2), Cm(2.2)

normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(11)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.line_spacing = 1.15

for name, size, before in [("Heading 1", 15, 16), ("Heading 2", 12.5, 10), ("Heading 3", 11.5, 8)]:
    st = doc.styles[name]
    st.font.name = "Calibri"
    st.element.rPr.rFonts.set(qn("w:asciiTheme"), "")
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.color.rgb = ACCENT
    st.paragraph_format.space_before = Pt(before)
    st.paragraph_format.space_after = Pt(4)
    st.paragraph_format.keep_with_next = True

cap = doc.styles["Caption"]
cap.font.size = Pt(9)
cap.font.italic = True
cap.font.color.rgb = INK2


# -- helpers --
def add_runs(p, text):
    """Add text with **bold** and *italic* markup."""
    import re
    for part in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text):
        if not part:
            continue
        if part.startswith("**"):
            p.add_run(part[2:-2]).bold = True
        elif part.startswith("*"):
            p.add_run(part[1:-1]).italic = True
        else:
            p.add_run(part)
    return p


def para(text, style=None, align=None, space_after=None):
    p = doc.add_paragraph(style=style)
    add_runs(p, text)
    if align is not None:
        p.alignment = align
    if space_after is not None:
        p.paragraph_format.space_after = Pt(space_after)
    return p


def bullets(items, style="List Bullet"):
    for it in items:
        p = doc.add_paragraph(style=style)
        p.paragraph_format.space_after = Pt(3)
        add_runs(p, it)


def h(text, level):
    return doc.add_heading(text, level=level)


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def table(rows, widths_cm, header=True, font_size=9.5):
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.cell(i, j)
            c.width = Cm(widths_cm[j])
            c.text = ""
            p = c.paragraphs[0]
            p.paragraph_format.keep_with_next = True  # keep the table together and with its caption
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            add_runs(p, str(val))
            for r in p.runs:
                r.font.size = Pt(font_size)
                if header and i == 0:
                    r.bold = True
            if header and i == 0:
                shade(c, HEADER_FILL)
    return t


def caption(text):
    p = doc.add_paragraph(style="Caption")
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(10)
    add_runs(p, text)
    return p


def figure(name, width_cm, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(FIG / name), width=Cm(width_cm))
    caption(text).alignment = WD_ALIGN_PARAGRAPH.CENTER


def page_number_footer(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    for tag, text in [("begin", None), (None, "PAGE"), ("end", None)]:
        if tag:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), tag)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = text
        run._r.append(el)
    run.font.size = Pt(9)
    run.font.color.rgb = INK2


# -- title page --
for _ in range(5):
    doc.add_paragraph()
para("Universidad de Castilla-La Mancha · Minería de Datos", align=WD_ALIGN_PARAGRAPH.CENTER).runs[0].font.color.rgb = INK2
p = para("Deliverable 1: Problem Definition", align=WD_ALIGN_PARAGRAPH.CENTER)
p.runs[0].font.size = Pt(13)
p.runs[0].font.color.rgb = INK2
doc.add_paragraph()
p = para("Forecasting Reservoir Storage and Drought States in the Tajo, Guadiana and Júcar Basins",
         align=WD_ALIGN_PARAGRAPH.CENTER)
p.runs[0].font.size = Pt(22)
p.runs[0].bold = True
p.runs[0].font.color.rgb = ACCENT
p = para("With a focus on the headwater reservoirs of Castilla-La Mancha and the Tajo-Segura transfer",
         align=WD_ALIGN_PARAGRAPH.CENTER)
p.runs[0].font.size = Pt(12.5)
p.runs[0].italic = True
for _ in range(6):
    doc.add_paragraph()
for name in ["Ayça Görgülü", "Mina Özdoğan", "Beyza Nur Balota"]:
    p = para(name, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    p.runs[0].font.size = Pt(12)
doc.add_paragraph()
para("29 October 2026", align=WD_ALIGN_PARAGRAPH.CENTER).runs[0].font.color.rgb = INK2

# Footer is defined once and inherited by later sections; the title page has none
doc.sections[0].different_first_page_header_footer = True
page_number_footer(doc.sections[0])
doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

# -- 1. Introduction --
h("1. Introduction and Motivation", 1)
para("Spain stores about 56,000 hm³ of water in roughly 375 large reservoirs. This water supplies cities, irrigates "
     "crops (the largest user), generates hydropower and feeds transfers between river basins. Rainfall in Spain is "
     "highly variable from one year to the next, and multi-year droughts are frequent (1992-95, 2005-08, 2017-19, "
     "2022-24). Reservoir storage is therefore the main variable that water authorities watch when they declare "
     "drought scenarios and restrict water use.")
para("Castilla-La Mancha is at the head of three major basins: the **Tajo**, the **Guadiana** and the **Júcar**. Their "
     "headwater reservoirs are strategic far beyond the region. The **Entrepeñas-Buendía** system (Guadalajara and "
     "Cuenca) is the source of the **Tajo-Segura transfer** to Murcia and Alicante. The amount transferred each month "
     "is fixed by law (Real Decreto 773/2014, amended by RD 638/2021) according to how much water these two reservoirs "
     "hold. **Alarcón** and **Contreras** (Cuenca) regulate the Júcar, which supplies Valencia and the irrigated "
     "plains of Albacete. Since the 2014 rules came into force, our data show that the Entrepeñas-Buendía system "
     "was below the “exceptional situation” threshold (level 3 or 4) in **52% of months** (75 of 145).")
para("Knowing **months in advance** whether these reservoirs will recover or fall further would let farmers, cities "
     "and basin authorities prepare. Today, the official drought indicators only describe the **current** situation "
     "(Haro-Monteagudo et al., 2017). This project uses data mining to forecast reservoir storage and the official "
     "states that depend on it.")

# -- 2. Data --
h("2. Description of the Original Data", 1)
h("2.1 Source", 2)
para("The main dataset is the **reservoir database of the Spanish Hydrological Bulletin** (*Base de datos del Boletín "
     "Hidrológico*, file **BD-Embalses**), published openly by the Ministry for the Ecological Transition (MITECO). "
     "It is distributed as a Microsoft Access file (.mdb, 213 MB). It contains a single table, "
     "*T_Datos Embalses 1988-2026*, with one row per reservoir and week. The bulletin is updated every week.")
h("2.2 What the data represent", 2)
para("Each record is the amount of water stored in one reservoir on one date (one measurement per week). The table "
     "has six fields (Table 1). We translated the field names into English, converted the Spanish number format "
     "(“1.234,56”) into numbers, and added the derived variable *pct_full* (stored water as a percentage of capacity).")
table([
    ["Original field", "Our name", "Type", "Description"],
    ["AMBITO_NOMBRE", "basin", "text", "River basin district (16 values, e.g. Tajo, Guadiana, Júcar)"],
    ["EMBALSE_NOMBRE", "reservoir", "text", "Reservoir name (402 values)"],
    ["FECHA", "date", "date", "Date of the weekly measurement"],
    ["AGUA_TOTAL", "capacity_hm3", "number", "Total capacity of the reservoir (hm³)"],
    ["AGUA_ACTUAL", "stored_hm3", "number", "Water currently stored (hm³)"],
    ["ELECTRICO_FLAG", "hydro_flag", "0/1", "1 if the reservoir is used for hydropower"],
    ["(derived)", "pct_full", "number", "stored_hm3 / capacity_hm3 × 100"],
], [3.3, 2.7, 1.5, 8.9])
caption("Table 1. Fields of the BD-Embalses table and their English names.")

h("2.3 Volume", 2)
table([
    ["Measure", "Value"],
    ["Records (rows)", "724,217"],
    ["Period", "6 Oct 1987 - 27 Oct 2026 (2,028 weeks, 39 years)"],
    ["Basins / reservoirs", "16 basins, 402 reservoirs (285 reporting in 1988, 375 in 2026)"],
    ["Total capacity (latest week)", "56,049 hm³, of which 31,809 hm³ stored (56.8% full)"],
    ["Focus subset (Tajo, Guadiana, Júcar)", "114 reservoirs, 217,717 rows"],
], [6.0, 10.4])
caption("Table 2. Size of the dataset.")

h("2.4 Scope of the project", 2)
para("We describe the whole national dataset, but the project focuses on the **Tajo, Guadiana and Júcar basins** "
     "(114 reservoirs, 23,440 hm³ of capacity, 42% of Spain’s total). The three rivers rise in Castilla-La Mancha, "
     "but their basins also extend into Madrid, Castilla y León, Extremadura, Andalucía, Aragón and the Valencia "
     "region (the Júcar water district also includes the Turia and Mijares rivers). The study area is therefore "
     "the **three complete basins**, not only Castilla-La Mancha. The **Duero basin** (35 reservoirs) is used only "
     "as a reference for comparison, because it is the Spanish basin studied by Baron et al. (2026). Within the "
     "study area, four reservoirs in Castilla-La Mancha receive special attention because they control the "
     "region’s main water decisions:")
table([
    ["Reservoir", "Basin", "Capacity", "Lowest % (date range 1988-2026)", "Highest %"],
    ["Entrepeñas", "Tajo", "886 hm³", "6.0%", "86.8%"],
    ["Buendía", "Tajo", "1,705 hm³", "4.2%", "59.7%"],
    ["Alarcón", "Júcar", "1,118 hm³", "2.5%", "81.3%"],
    ["Contreras", "Júcar", "874 hm³", "1.7%", "93.6%"],
], [3.2, 2.2, 2.6, 5.4, 3.0])
caption("Table 3. Key reservoirs. Combined Entrepeñas + Buendía storage ranged from 124 hm³ (October 1995) to "
        "1,682 hm³ (March 2026).")

h("2.5 Data quality", 2)
para("A first exploratory analysis (Annex A) found three issues that the cleaning step will handle:")
bullets([
    "**Placeholder rows:** 18,867 rows (71 reservoirs, mostly before 1999) have capacity and storage equal to 0. "
    "They correspond to reservoirs not yet included in the bulletin and will be removed.",
    "**Storage above capacity:** 1,264 rows in 90 reservoirs (median 107% full). These are probably flood surcharge "
    "or capacity values that changed over time. They will be capped or flagged.",
    "**Missing values:** only 2 values (2003).",
])
para("A key exploratory finding is that the reservoirs in our basins behave very differently from those in northern "
     "Spain. We measured the **seasonal share**: the fraction of each reservoir’s variation that is explained by its "
     "average yearly cycle. It is 0.34 in the Duero basin but only 0.15 in the Tajo, 0.07 in the Guadiana and 0.06 in "
     "the Júcar, and just 0.02-0.07 for the four key reservoirs (Annex A, Table A3). These are **hyperannual** "
     "reservoirs: their storage changes more between years than within a year (Figures A1 and A4). This finding "
     "shapes our hypotheses (Section 4).")

# -- 3. Related work --
h("3. Background and Related Work", 1)
para("We reviewed eleven studies in three groups. Table 4 summarises them and what we take from each.")

h("3.1 Machine learning for reservoir forecasting", 2)
para("**Baron et al. (2026)** is the closest work. They trained a single *Gradient Boosting* model for 33 reservoirs in "
     "the UK, Spain and France to forecast monthly storage 1 and 3 months ahead, using lagged storage, rainfall and "
     "temperature, and static catchment features. The model reached a median NSE (Nash-Sutcliffe efficiency, where "
     "1 is a perfect forecast) of 0.93 at one month and 0.80 at three months, and beat a SARIMAX benchmark. "
     "However, **all 15 Spanish reservoirs were in the Duero basin**, the model **failed on reservoirs without a "
     "clear seasonal signal** (NSE 0.20), and it used **no data on human operations**. **García-Feal et al. (2022)** "
     "compared linear regression and three neural networks (MLP, NARX, LSTM) to forecast next-day outflow of eight "
     "reservoirs in the wet Miño-Sil basin. NARX was best, but the authors warn that the results may not carry over "
     "to drier climates. Studies on dams in California (Rao et al., 2026) and Türkiye (Güneş Şen, 2025) found that "
     "tree ensembles (Random Forest, XGBoost) perform as well as or better than deep learning for reservoirs "
     "operated by rules.")

h("3.2 Drought and reservoirs in Spain", 2)
para("**Vicente-Serrano & López-Moreno (2005)** showed that reservoir storage (Yesa, Ebro basin) responds to rainfall "
     "accumulated over about **8 months** (correlation 0.59 with the 8-month SPI drought index), much longer than "
     "rivers (2 months). **Lorenzo-Lacruz et al. (2010)** studied our exact area, the Tajo headwaters. They found "
     "that drought has dominated since the 1970s, that SPEI (which includes temperature) explains storage slightly "
     "better than SPI, and that the link between climate and storage changed after the transfers began. "
     "**Torelló-Sentelles & Franzke (2022)** used Random Forest to predict drought impacts in Spanish regions. "
     "Long accumulation periods (15-33 months) and climate patterns such as the NAO and WeMO were among the best "
     "predictors. However, they used random cross-validation, which ignores the order of time.")

h("3.3 Drought early warning and the Tajo-Segura transfer", 2)
para("**Haro-Monteagudo et al. (2017)** explain that Spain’s official drought *State Index* only compares current "
     "values with history and has “low, or even non-existent” forecasting ability. They forecast the probability of "
     "changing drought scenario in the Júcar 1-3 years ahead using an optimisation model of the whole water system "
     "driven by simulated river flows. The method needs a calibrated model and deep knowledge of the system, and no "
     "accuracy score is reported. They also note that Alarcón and Contreras are operated over several years, which "
     "agrees with our seasonal-share result. A 2025 master’s thesis at UPV (**Jiménez Cando, 2025**) forecasts a "
     "rainfall-based drought indicator for the Júcar using past analogue years and ECMWF seasonal forecasts, without "
     "machine learning. It names measuring forecast skill and extending the method to the storage-dependent "
     "scarcity index as future work, and notes that the new drought plan (PES 2024) will require such forecasts. "
     "Finally, **Pellicer-Martínez & Martínez-Paz (2018)** and **Senent-Aparicio et al. (2021)** project large falls "
     "in inflows to Entrepeñas-Buendía under climate change (up to 40-53%) and in transferable water (60-79%) for "
     "the second half of the century. They use physical models and long-term scenarios, not short-term forecasts.")

table([
    ["Study", "What it does", "What we take from it"],
    ["Baron et al. 2026", "Gradient Boosting, many reservoirs, monthly storage 1-3 months ahead",
     "Baseline design; their stated gaps (weak seasonality, no operations data, no Tajo/Guadiana/Júcar)"],
    ["García-Feal et al. 2022", "ANNs vs. linear regression for daily outflow, Miño-Sil",
     "Persistence baseline, chronological split; may not transfer to dry basins"],
    ["Rao et al. 2026; Güneş Şen 2025", "RF / XGBoost vs. deep learning for dams",
     "Tree ensembles suit rule-operated reservoirs"],
    ["Vicente-Serrano & López-Moreno 2005", "SPI time scales vs. storage and flow",
     "Storage responds to ~8-month accumulated rainfall"],
    ["Lorenzo-Lacruz et al. 2010, 2013", "Drought and management in the Tajo headwaters",
     "SPEI and management matter; reservoirs delay drought signals"],
    ["Torelló-Sentelles & Franzke 2022", "RF for drought impacts in Spain",
     "Use long windows and NAO/WeMO; avoid random CV"],
    ["Haro-Monteagudo et al. 2017", "Optimisation-based early warning, Júcar",
     "Official State Index and thresholds; no skill score; critique of history-based methods"],
    ["Jiménez Cando 2025 (UPV)", "Analogue + ECMWF forecasts of drought index, Júcar",
     "PES 2024 requires forecasts; no ML, no skill evaluation"],
    ["Pellicer-Martínez 2018; Senent-Aparicio 2021", "Climate-change impact on the transfer",
     "Stakes and transfer rules; long-term, not operational"],
], [4.0, 5.8, 6.6], font_size=9)
caption("Table 4. Summary of related work.")

h("3.4 Gap addressed by this project", 2)
para("To our knowledge, no study has used data mining to forecast reservoir storage and the official drought and "
     "transfer states in the semi-arid, hyperannual headwater reservoirs of the Tajo, Guadiana and Júcar. The best "
     "existing machine-learning model is known to fail on exactly this type of reservoir, and the existing early "
     "warning methods for the region are either descriptive or depend on complex system models without reported "
     "skill.")

# -- 4. Hypotheses and objectives --
h("4. Hypotheses and objectives", 1)
h("4.1 Problem statement", 2)
para("*Given the storage history of a reservoir and information about recent climate, can we predict its storage "
     "and its official drought or transfer state several months ahead, accurately enough to support decisions?*")

h("4.2 Intelligence component", 2)
para("A descriptive study would report how full the reservoirs are now, or plot their history. Our project instead "
     "**builds models that learn** from 39 years of data how storage responds to accumulated rainfall, temperature, "
     "season and past storage, and **uses them on new, unseen periods** to:")
bullets([
    "**predict** future storage (regression),",
    "**classify** the future official state (classification), and",
    "**discover** groups of reservoirs with similar behaviour (clustering).",
])
para("The models are evaluated by how well they predict the future, not by how well they describe the past.")

h("4.3 Objectives", 2)
para("**O1. Storage forecasting (regression).** Forecast monthly storage (% full) 1, 3 and 6 months ahead for the "
     "114 reservoirs of the Tajo, Guadiana and Júcar, and for the combined Entrepeñas-Buendía and Alarcón-Contreras "
     "systems. Add long-memory features to a Baron-style Gradient Boosting baseline: rainfall and SPI/SPEI "
     "accumulated over 12-36 months, the NAO and WeMO climate patterns, and the reservoir’s position in its "
     "multi-year cycle.")
para("**O2. Official state forecasting (classification).** Predict, 1-6 months ahead:")
bullets([
    "the **drought state** of Alarcón-Contreras and other systems (Normal, Pre-alert, Alert, Emergency), computed "
    "from storage with the official State Index formula (Haro-Monteagudo et al., 2017). In our data, the four "
    "classes cover 49%, 23%, 13% and 15% of months, which gives a usable class balance;",
    "the **Tajo-Segura transfer level** (1-4) under RD 638/2021. Since October 2014, the storage-based level was "
    "1 in 15 months, 2 in 55, 3 in 58 and 4 in 17.",
])
para("**O3. Reservoir typology (clustering).** Group the 114 reservoirs by the shape of their storage series "
     "(seasonal share, yearly cycle, response to drought, recovery speed) using k-means or hierarchical clustering, "
     "and test whether forecast accuracy differs between the groups.")

h("4.4 Hypotheses", 2)
table([
    ["", "Hypothesis", "How we test it"],
    ["H1", "Hyperannual reservoirs are poorly predicted by a Baron-style model that only looks back ≤12 months.",
     "Compare model skill against seasonal share and reservoir cluster"],
    ["H2", "Long-memory features (12-36-month rainfall, SPI/SPEI, NAO/WeMO) improve 3-6-month forecasts for "
     "hyperannual reservoirs.", "Same model with and without these features, on the test period"],
    ["H3", "Forecasting storage first and then applying the official rules predicts the drought state and transfer "
     "level better than classifying the state directly from current indicators.",
     "Compare macro-F1 of both approaches against a “state stays the same” baseline"],
    ["H4", "Reservoirs form distinct groups (seasonal vs. hyperannual) that need different models.",
     "Cluster quality (silhouette) and skill per cluster"],
], [1.0, 9.0, 6.4], font_size=9)
caption("Table 5. Hypotheses and how each will be tested.")

h("4.5 Evaluation plan", 2)
bullets([
    "**Time-based split:** train on 1988-2016, validate on 2017-2020, and test on 2021-2026. The test period "
    "contains the 2022-24 drought, the 2025-26 recovery and the period after the 2021 rule change. No random splits.",
    "**Baselines:** persistence (next month = this month), monthly climatology (the historical average for that "
    "month), a historical-analogue method, and the Baron et al. (2026) feature set.",
    "**Metrics:** NSE, RMSE and bias for storage; macro-F1, a confusion matrix and recall of the most severe classes "
    "for the states.",
    "**Answering the critique** that “modelling the past to anticipate future drought is an ineffective and risky "
    "approach” (Haro-Monteagudo et al., 2017): we test only on periods the model has never seen and report how "
    "accuracy changes over time.",
])

# -- 5. Enrichment --
h("5. Possibilities for data enrichment", 1)
para("The reservoir data alone describe *what* happens to storage but not *why*. Table 6 lists public datasets that "
     "can be joined to explain and predict it.")
table([
    ["Dataset (source)", "Variables", "Join key", "Use"],
    ["AEMET OpenData (free API key)", "Daily rainfall and temperature at stations in Guadalajara, Cuenca, Teruel, "
     "Albacete, Ciudad Real", "Date + catchment", "Accumulated rainfall, SPI/SPEI (O1, O2)"],
    ["Copernicus ERA5 reanalysis", "Gridded rainfall, temperature, snow, evaporation", "Date + catchment polygon",
     "Catchment averages; snow for Entrepeñas-Buendía"],
    ["SAIH Tajo / CEDEX Anuario de Aforos", "Reservoir inflows and outflows", "Date + reservoir",
     "12-month inflow needed for transfer level 1; water balance"],
    ["MITECO drought monitoring reports (PES)", "Official monthly scarcity indices by territorial unit",
     "Month + unit", "Official labels to validate O2"],
    ["Comisión Central de Explotación del Acueducto Tajo-Segura (BOE orders)",
     "Declared transfer level and volume each month", "Month", "Ground truth for the transfer level"],
    ["NOAA Climate Prediction Center", "NAO (North Atlantic Oscillation) index", "Month",
     "Long-range rainfall predictor"],
    ["Univ. of Barcelona climatology group", "WeMO (Western Mediterranean Oscillation) index", "Month",
     "Rainfall predictor for eastern Spain"],
    ["INE; Ministry of Agriculture (ESYRCE)", "Population; irrigated area by province", "Year + province",
     "Demand proxies"],
    ["Red Eléctrica (REE)", "Hydropower generation", "Date", "Releases for electricity"],
], [4.4, 4.8, 2.8, 4.4], font_size=9)
caption("Table 6. Public datasets for enrichment.")

# -- 6. Risks --
h("6. Expected difficulties", 1)
bullets([
    "**Human operation:** releases depend on management decisions, not only on climate. Transfer volumes and "
    "hydropower data partly capture this.",
    "**Different time resolutions:** weekly storage, daily weather, monthly indices. Everything will be aggregated "
    "to months.",
    "**Spatial matching:** weather stations or grid cells must be assigned to each reservoir’s catchment.",
    "**Changing conditions:** inflows to the Tajo headwaters have fallen since the 1980s, and the rules changed in "
    "2014 and 2021. The time-based test is designed to expose this.",
    "**Approximate labels:** our State Index uses storage only, while the official index also uses rainfall, river "
    "flow and groundwater. Without inflow data, the transfer level ignores the 12-month inflow condition. We will "
    "validate both against official records where available.",
])

# -- References --
h("References", 1)
refs = [
    "Baron, H. E., Rickards, N. J., Chengot, R., & Keller, V. J. D. (2026). Subseasonal to seasonal prediction and "
    "forecasting of reservoir storage using a machine learning model in the UK, Spain and France. *International "
    "Journal of River Basin Management*. https://doi.org/10.1080/15715124.2026.2729476",
    "García-Feal, O., González-Cao, J., Fernández-Nóvoa, D., Astray Dopazo, G., & Gómez-Gesteira, M. (2022). "
    "Comparison of machine learning techniques for reservoir outflow forecasting. *Natural Hazards and Earth System "
    "Sciences, 22*, 3859-3874. https://doi.org/10.5194/nhess-22-3859-2022",
    "Güneş Şen, S. (2025). Machine learning-based water level forecast in a dam reservoir: A case study of Karaçomak "
    "Dam in the Kızılırmak Basin, Türkiye. *Sustainability, 17*(18). https://doi.org/10.3390/su17188378",
    "Haro-Monteagudo, D., Solera, A., & Andreu, J. (2017). Drought early warning based on optimal risk forecasts in "
    "regulated river systems: Application to the Jucar River Basin (Spain). *Journal of Hydrology, 544*, 36-45. "
    "https://doi.org/10.1016/j.jhydrol.2016.11.022",
    "Jiménez Cando, D. (2025). *Predicción estacional de los indicadores de sequía prolongada en la Demarcación "
    "Hidrográfica del Júcar* [Master’s thesis]. Universitat Politècnica de València.",
    "Lorenzo-Lacruz, J., Vicente-Serrano, S. M., López-Moreno, J. I., Beguería, S., García-Ruiz, J. M., & Cuadrat, "
    "J. M. (2010). The impact of droughts and water management on various hydrological systems in the headwaters "
    "of the Tagus River (central Spain). *Journal of Hydrology, 386*, 13-26. "
    "https://doi.org/10.1016/j.jhydrol.2010.01.001",
    "Lorenzo-Lacruz, J., et al. (2013). Hydrological drought response to meteorological drought in the Iberian "
    "Peninsula. *Climate Research, 58*(2), 117-131.",
    "Ministerio para la Transición Ecológica y el Reto Demográfico (MITECO). (2026). *Base de datos del Boletín "
    "Hidrológico (BD-Embalses)* [Data set].",
    "Pellicer-Martínez, F., & Martínez-Paz, J. M. (2018). Climate change effects on the hydrology of the headwaters "
    "of the Tagus River: Implications for the management of the Tagus-Segura transfer. *Hydrology and Earth System "
    "Sciences, 22*, 6473-6491. https://doi.org/10.5194/hess-22-6473-2018",
    "Rao, M. M., et al. (2026). Reassessing model complexity in reservoir outflow forecasting: A multi-site, "
    "physics-informed benchmark of deep learning and ensemble methods. *Ecological Engineering & Environmental "
    "Technology, 27*(3), 239-252.",
    "Real Decreto 638/2021, de 27 de julio, por el que se modifica el Real Decreto 773/2014 (reglas de explotación "
    "del trasvase Tajo-Segura). *Boletín Oficial del Estado*.",
    "Senent-Aparicio, J., et al. (2021). A modelling approach to forecast the effect of climate change on the "
    "Tagus-Segura interbasin water transfer. *Water Resources Management, 35*. "
    "https://doi.org/10.1007/s11269-021-02919-y",
    "Torelló-Sentelles, H., & Franzke, C. L. E. (2022). Drought impact links to meteorological drought indicators "
    "and predictability in Spain. *Hydrology and Earth System Sciences, 26*, 1821-1844. "
    "https://doi.org/10.5194/hess-26-1821-2022",
    "Vicente-Serrano, S. M., & López-Moreno, J. I. (2005). Hydrological response to different time scales of "
    "climatological drought: An evaluation of the Standardized Precipitation Index in a mountainous Mediterranean "
    "basin. *Hydrology and Earth System Sciences, 9*, 523-533. https://doi.org/10.5194/hess-9-523-2005",
]
for r in refs:
    p = para(r, space_after=4)
    p.paragraph_format.left_indent = Cm(0.8)
    p.paragraph_format.first_line_indent = Cm(-0.8)
    for run in p.runs:
        run.font.size = Pt(9.5)

# -- Annex --
doc.add_section(WD_SECTION.NEW_PAGE)
h("Annex A. Exploratory data analysis", 1)
para("All statistics and figures were produced with Python (pandas, matplotlib) from BD-Embalses after removing "
     "the placeholder rows.")

h("A.1 Reservoirs per basin", 2)
table([
    ["Basin", "Reservoirs", "Capacity (hm³)", "Stored (hm³)", "% full"],
    ["**Tajo**", "51", "11,056", "5,728", "51.8"],
    ["**Guadiana**", "39", "9,538", "6,835", "71.7"],
    ["Guadalquivir", "47", "8,030", "5,495", "68.4"],
    ["Ebro", "76", "7,813", "3,513", "45.0"],
    ["Duero", "35", "7,602", "3,445", "45.3"],
    ["Miño - Sil", "29", "3,030", "1,517", "50.1"],
    ["**Júcar**", "23", "2,846", "1,482", "52.1"],
    ["Other 9 basins", "75", "6,134", "3,794", "61.9"],
    ["**Total**", "375", "56,049", "31,809", "56.8"],
], [4.4, 2.4, 3.2, 3.2, 2.2])
caption("Table A1. Reservoirs per basin in the latest week (27 October 2026). Focus basins in bold.")

h("A.2 Data quality summary", 2)
table([
    ["Issue", "Rows", "Reservoirs", "Action"],
    ["Capacity and storage = 0 (not yet in the bulletin)", "18,867", "71", "Remove"],
    ["Storage > capacity", "1,264", "90", "Cap at 100% or flag"],
    ["Missing capacity / storage", "2", "-", "Interpolate"],
], [7.0, 2.2, 2.4, 4.8])
caption("Table A2. Data quality issues.")

h("A.3 Seasonality", 2)
table([
    ["Basin / reservoir", "Reservoirs", "Seasonal share (median)"],
    ["Duero (used by Baron et al., 2026)", "33", "0.34"],
    ["Tajo", "51", "0.15"],
    ["Guadiana", "36", "0.07"],
    ["Júcar", "23", "0.06"],
    ["Entrepeñas / Buendía", "-", "0.04 / 0.07"],
    ["Alarcón / Contreras", "-", "0.03 / 0.02"],
    ["La Serena / Cíjara (Guadiana)", "-", "0.01 / 0.05"],
], [7.6, 2.6, 4.6])
caption("Table A3. Share of the variation in monthly % full explained by the average yearly cycle "
        "(reservoirs with at least 10 years of data).")

h("A.4 Figures", 2)
figure("fig1_entrepenas_buendia.png", 16, "Figure A1. Combined storage of Entrepeñas and Buendía, 1988-2026. The "
       "system swings over several years rather than within a year.")
figure("fig2_basins_pct_full.png", 16, "Figure A2. Monthly storage (% full) of the Tajo, Guadiana and Júcar basins. "
       "Drought periods (1992-95, 2005-08, 2017-19, 2022-24) are visible.")
figure("fig3_seasonal_pattern.png", 16, "Figure A3. Typical yearly cycle per basin: median and middle 50% of years. "
       "The wide bands show that year-to-year differences are larger than the seasonal cycle.")
figure("fig4_annual_heatmap.png", 16, "Figure A4. Annual mean storage per basin. Pale cells mark drought years.")
figure("fig5_coverage.png", 15, "Figure A5. Number of reservoirs reporting to the bulletin each year.")

h("Annex B. Tajo-Segura transfer rules (RD 638/2021)", 1)
table([
    ["Level", "Condition (Entrepeñas + Buendía, start of month)", "Monthly transfer"],
    ["1", "Storage ≥ 1,300 hm³ or inflow in the previous 12 months ≥ 1,400 hm³", "60 hm³"],
    ["2", "Storage < 1,300 hm³ and 12-month inflow < 1,400 hm³, above the level 3 threshold", "27 hm³"],
    ["3", "Storage at or below the monthly threshold (586-688 hm³, see below)", "Up to 20 hm³ (discretionary)"],
    ["4", "Storage < 400 hm³", "0"],
], [1.4, 10.6, 4.4])
doc.add_paragraph().paragraph_format.keep_with_next = True
table([
    ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"],
    ["613", "609", "605", "602", "597", "591", "586", "645", "673", "688", "661", "631"],
], [1.36] * 12, font_size=9)
caption("Table B1. Transfer levels and level 3 thresholds (hm³). Maximum 650 hm³ per hydrological year. "
        "RD 638/2021 changed the level 2 volume (38 → 27 hm³) and the 12-month inflow threshold (1,200 → 1,400 hm³).")

doc.save(OUT)
print("saved", OUT)
