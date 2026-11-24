"""Build Deliverable 1 as a Word document in ACM (sigconf-style) two-column format, max 5 pages."""
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

HERE = Path(__file__).parent
FIG = HERE.parent.parent / "figures"
# Writes a regenerated copy; the submitted version (edited by hand) is Deliverable1.pdf.
OUT = HERE / "Deliverable1_ACM_generated.docx"

SERIF, SANS = "Times New Roman", "Arial"
BODY_PT, SMALL_PT = 9.5, 8

doc = Document()

# ---------- page: US Letter, ACM text block 7 x 9.25 in ----------
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
sec.left_margin = sec.right_margin = Inches(0.75)
sec.top_margin, sec.bottom_margin = Inches(0.8), Inches(0.9)

normal = doc.styles["Normal"]
normal.font.name = SERIF
normal.font.size = Pt(BODY_PT)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), SERIF)
normal.paragraph_format.space_after = Pt(0)
normal.paragraph_format.line_spacing = 1.0
normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

for name, size in [("Heading 1", 9.5), ("Heading 2", 9.5)]:
    st = doc.styles[name]
    st.font.name = SANS
    st.element.rPr.rFonts.set(qn("w:asciiTheme"), "")
    st.element.rPr.rFonts.set(qn("w:hAnsiTheme"), "")
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.italic = False
    st.font.color.rgb = None
    st.paragraph_format.space_before = Pt(9 if name == "Heading 1" else 6)
    st.paragraph_format.space_after = Pt(3)
    st.paragraph_format.keep_with_next = True


def set_columns(section, num, space_in=0.33):
    cols = section._sectPr.find(qn("w:cols"))
    if cols is None:
        cols = OxmlElement("w:cols")
        section._sectPr.append(cols)
    cols.set(qn("w:num"), str(num))
    cols.set(qn("w:space"), str(int(space_in * 1440)))


def add_runs(p, text, size=None, font=None):
    """Add text with **bold** and *italic* markup."""
    for part in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text):
        if not part:
            continue
        if part.startswith("**"):
            r = p.add_run(part[2:-2])
            r.bold = True
        elif part.startswith("*"):
            r = p.add_run(part[1:-1])
            r.italic = True
        else:
            r = p.add_run(part)
        if size:
            r.font.size = Pt(size)
        if font:
            r.font.name = font
    return p


def para(text, indent=True, size=None, align=None, after=0, before=0, font=None):
    p = doc.add_paragraph()
    add_runs(p, text, size, font)
    pf = p.paragraph_format
    pf.first_line_indent = Inches(0.13) if indent else None
    pf.space_after, pf.space_before = Pt(after), Pt(before)
    if align is not None:
        p.alignment = align
    return p


def h1(text):
    return doc.add_heading(text.upper(), level=1)


def h2(text):
    return doc.add_heading(text, level=2)


def bullets(items):
    for it in items:
        p = doc.add_paragraph(style="List Bullet")
        add_runs(p, it)
        p.paragraph_format.space_after = Pt(1)
        for r in p.runs:
            r.font.size = Pt(BODY_PT)


def border(cell, edges):
    tcPr = cell._tc.get_or_add_tcPr()
    b = OxmlElement("w:tcBorders")
    for edge, sz in edges.items():
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), str(sz))
        e.set(qn("w:color"), "000000")
        b.append(e)
    tcPr.append(b)


def caption(text, before=4, after=2):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.size = Pt(SMALL_PT)
    r.font.name = SANS
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(before), Pt(after)
    return p


def table(caption_text, rows, widths_in, size=SMALL_PT):
    """ACM style: caption above, rules only at top, under the header and at the bottom."""
    caption(caption_text, before=6).paragraph_format.keep_with_next = True
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    last = len(rows) - 1
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.cell(i, j)
            c.width = Inches(widths_in[j])
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.keep_with_next = i < last
            add_runs(p, val, size)
            if i == 0:
                for r in p.runs:
                    r.bold = True
                border(c, {"top": 8, "bottom": 4})
            elif i == last:
                border(c, {"bottom": 8})
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def figure(name, width_in, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(FIG / name), width=Inches(width_in))
    caption(text, after=6)


def page_numbers(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    for tag, text in [("begin", None), (None, "PAGE"), ("end", None)]:
        el = OxmlElement("w:fldChar" if tag else "w:instrText")
        if tag:
            el.set(qn("w:fldCharType"), tag)
        else:
            el.set(qn("xml:space"), "preserve")
            el.text = text
        run._r.append(el)
    run.font.size = Pt(SMALL_PT)


COL_W = 3.33  # column width in inches

# ---------- title block (one column) ----------
set_columns(sec, 1)
page_numbers(sec)
p = para("Forecasting Reservoir Storage and Drought States in the Tajo, Guadiana and Júcar Basins",
         indent=False, size=16, align=WD_ALIGN_PARAGRAPH.CENTER, font=SANS, after=2)
p.runs[0].bold = True
para("Deliverable 1: Problem Definition. Minería de Datos, Universidad de Castilla-La Mancha", indent=False,
     size=11, align=WD_ALIGN_PARAGRAPH.CENTER, font=SANS, after=10)

authors = doc.add_table(rows=2, cols=3)
authors.alignment = WD_TABLE_ALIGNMENT.CENTER
for j, name in enumerate(["Ayça Görgülü", "Mina Özdoğan", "Beyza Nur Balota"]):
    for i, (txt, sz) in enumerate([(name, 11), ("Universidad de Castilla-La Mancha\nSpain", 9)]):
        c = authors.cell(i, j)
        c.width = Inches(2.33)
        lines = txt.split("\n")
        cp = c.paragraphs[0]
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cp.add_run(lines[0])
        r.font.size = Pt(sz)
        r.font.name = SANS
        for extra in lines[1:]:
            r.add_break()
            r2 = cp.add_run(extra)
            r2.font.size = Pt(sz)
            r2.font.name = SANS

h1("Abstract").paragraph_format.space_before = Pt(12)
para("Reservoir storage is the main variable that Spanish water authorities use to declare drought scenarios and to "
     "fix the monthly volume of the Tajo-Segura transfer, but the official indicators only describe the current "
     "situation. We propose a data-mining project that forecasts reservoir storage and the official states that "
     "depend on it, months in advance, for the 114 reservoirs of the Tajo, Guadiana and Júcar basins, with a focus on "
     "the headwater reservoirs of Castilla-La Mancha (Entrepeñas, Buendía, Alarcón and Contreras). The main data source "
     "is the open weekly reservoir database of the Spanish Hydrological Bulletin (724,217 records, 1987-2026). An "
     "exploratory analysis shows that these reservoirs are hyperannual: only 2-15% of their variation follows the "
     "yearly cycle, compared with 34% in the Duero basin, where the closest published machine-learning model was "
     "tested and where it fails on this type of reservoir. We define three objectives (storage regression, "
     "drought-state and transfer-level classification, and reservoir clustering), four testable hypotheses, an "
     "evaluation plan, the public data for enrichment, and a brief feasibility study.", indent=False)
para("**Keywords:** reservoir storage, drought forecasting, data mining, gradient boosting, clustering, "
     "Tajo-Segura transfer", indent=False, before=4, after=4)

# ---------- body (two columns) ----------
body = doc.add_section(WD_SECTION.CONTINUOUS)
set_columns(body, 2)

h1("1 Introduction")
para("Spain stores about 56,000 hm³ of water in roughly 375 large reservoirs that supply cities, irrigation (the "
     "largest user), hydropower and transfers between basins. Rainfall varies strongly between years and multi-year "
     "droughts are frequent (1992-95, 2005-08, 2017-19, 2022-24), so storage is the variable that basin authorities "
     "watch when they declare drought scenarios and restrict water use.", indent=False)
para("Castilla-La Mancha is at the head of three major basins: the Tajo, the Guadiana and the Júcar. The "
     "**Entrepeñas-Buendía** system is the source of the **Tajo-Segura transfer**, whose monthly volume is fixed by "
     "law according to the water stored in these two reservoirs (RD 773/2014, amended by RD 638/2021 [10]). Since the "
     "2014 rules came into force, our data show that the system was in an “exceptional” situation (level 3 or 4) in "
     "52% of months. **Alarcón** and **Contreras** regulate the Júcar, which supplies Valencia and the irrigated "
     "plains of Albacete. Knowing *months in advance* whether these reservoirs will recover or fall would help "
     "farmers, cities and authorities prepare, while the official drought indicators only describe the current "
     "state [4].")

h1("2 Data Source and Description")
h2("2.1 Source")
para("The main dataset is the reservoir database of the Spanish Hydrological Bulletin (*Base de datos del Boletín "
     "Hidrológico*, file BD-Embalses), published openly by the Ministry for the Ecological Transition (MITECO) [7]. "
     "It is a Microsoft Access file (213 MB) with one table, *T_Datos Embalses 1988-2026*, updated weekly. We "
     "converted it to CSV, translated the field names into English, converted the Spanish number format into "
     "numbers and added the derived variable *pct_full* (Table 1).", indent=False)
table("Table 1: Fields of BD-Embalses (one row per reservoir and week).", [
    ["Original field", "Our name", "Description"],
    ["AMBITO_NOMBRE", "basin", "River basin district (16)"],
    ["EMBALSE_NOMBRE", "reservoir", "Reservoir name (402)"],
    ["FECHA", "date", "Date of the weekly measurement"],
    ["AGUA_TOTAL", "capacity_hm3", "Total capacity (hm³)"],
    ["AGUA_ACTUAL", "stored_hm3", "Water stored (hm³)"],
    ["ELECTRICO_FLAG", "hydro_flag", "1 if used for hydropower"],
    ["(derived)", "pct_full", "Stored / capacity × 100"],
], [1.3, 0.85, 1.18])

h2("2.2 Volume and scope")
para("The table holds **724,217 records** for 402 reservoirs in 16 basins over 2,028 weeks (6 Oct 1987 to 27 Oct "
     "2026); 285 reservoirs reported in 1988 and 375 in 2026. Total capacity is 56,049 hm³, 56.8% full in the last "
     "week. The project focuses on the **Tajo, Guadiana and Júcar basins** (114 reservoirs, 217,717 records, "
     "23,440 hm³, 42% of Spain’s capacity). The three rivers rise in Castilla-La Mancha, but the basins also extend "
     "into Madrid, Castilla y León, Extremadura, Andalucía, Aragón and the Valencia region, so the study area is the "
     "three complete basins. The **Duero** basin (35 reservoirs) is used only as a reference, because it is the "
     "Spanish basin studied by Baron et al. [1]. Four reservoirs in Castilla-La Mancha receive special attention: "
     "Entrepeñas (886 hm³) and Buendía (1,705 hm³), whose combined storage ranged from 124 hm³ (October 1995) to "
     "1,682 hm³ (March 2026), and Alarcón (1,118 hm³) and Contreras (874 hm³).", indent=False)

h2("2.3 Data quality and first findings")
para("We found 18,867 placeholder rows with zero capacity (71 reservoirs not yet in the bulletin, mostly before "
     "1999), which will be removed; 1,264 rows above 100% (flood surcharge or changed capacities), which will be "
     "capped or flagged; and only 2 missing values.", indent=False)
para("The key exploratory finding is that the reservoirs in our basins behave very differently from those in "
     "northern Spain. We computed the **seasonal share**: the fraction of each reservoir’s monthly variation "
     "explained by its average yearly cycle (Table 2). Our reservoirs are **hyperannual**: their storage changes more "
     "between years than within a year (Figures 1 and 2).")
table("Table 2: Seasonal share of storage variation (median over reservoirs with at least 10 years of data).", [
    ["Basin or reservoir", "Reservoirs", "Seasonal share"],
    ["Duero (reference)", "33", "0.34"],
    ["Tajo", "51", "0.15"],
    ["Guadiana", "36", "0.07"],
    ["Júcar", "23", "0.06"],
    ["Entrepeñas / Buendía", "", "0.04 / 0.07"],
    ["Alarcón / Contreras", "", "0.03 / 0.02"],
], [1.6, 0.8, 0.93])
figure("acm_fig1_entrepenas_buendia.png", COL_W, "Figure 1: Combined storage of Entrepeñas and Buendía, 1988-2026. "
       "The system swings over several years rather than within a year.")

h1("3 Related Work")
para("**Machine learning for reservoirs.** The closest work is Baron et al. [1], who trained one Gradient Boosting "
     "model for 33 reservoirs in the UK, Spain and France to forecast monthly storage 1 and 3 months ahead (median "
     "NSE 0.93 and 0.80, better than SARIMAX). All their Spanish reservoirs are in the Duero basin, the model fails "
     "on reservoirs without a clear seasonal signal (NSE 0.20), and it uses no data on human operations. "
     "García-Feal et al. [2] compared linear regression and neural networks (MLP, NARX, LSTM) for next-day outflow "
     "in the wet Miño-Sil basin and warn that results may not transfer to dry climates. For rule-operated dams, tree "
     "ensembles perform as well as or better than deep learning [3, 9].", indent=False)
para("**Drought and reservoirs in Spain.** Reservoir storage responds to rainfall accumulated over about 8 months "
     "[13]. In the Tajo headwaters, drought has dominated since the 1970s, SPEI explains storage slightly better than "
     "SPI, and management changed the climate-storage link after the transfers began [6]. Random Forest predicts "
     "drought impacts in Spain, with 15-33-month accumulations and the NAO and WeMO climate patterns among the best "
     "predictors, although with random cross-validation [12].")
para("**Early warning and the transfer.** Haro-Monteagudo et al. [4] show that Spain’s official *State Index* has "
     "almost no forecasting ability and forecast drought scenarios in the Júcar 1-3 years ahead with an optimisation "
     "model of the whole system; the method needs a calibrated system model and reports no accuracy score. A recent "
     "thesis forecasts a rainfall-based drought indicator for the Júcar from past analogues and ECMWF forecasts, "
     "without machine learning, and notes that the new drought plans will require such forecasts [5]. Climate-change "
     "studies project inflows to Entrepeñas-Buendía falling by up to about 50% and transferable water by 60-79% later "
     "this century [8, 11], but they are long-term scenarios, not forecasts.")
para("**Gap.** To our knowledge, no study has used data mining to forecast storage and the official drought and "
     "transfer states in the semi-arid, hyperannual reservoirs of these basins, where the best existing model is "
     "known to fail.")

h1("4 Hypotheses and Objectives")
para("**Problem.** *Given a reservoir’s storage history and recent climate, can we predict its storage and its "
     "official drought or transfer state several months ahead, accurately enough to support decisions?*",
     indent=False)
para("**Intelligence component.** A descriptive study would report how full the reservoirs are now. Our models "
     "*learn* from 39 years of data how storage responds to accumulated rainfall, temperature, season and past "
     "storage, and are judged only on new, unseen periods. The project combines the three main data-mining tasks:")
bullets([
    "**O1, regression:** forecast monthly storage (% full) 1, 3 and 6 months ahead for the 114 reservoirs and the "
    "Entrepeñas-Buendía and Alarcón-Contreras systems, adding long-memory features (rainfall and SPI/SPEI over "
    "12-36 months, NAO and WeMO) to a Baron-style Gradient Boosting baseline.",
    "**O2, classification:** predict the *drought state* (Normal, Pre-alert, Alert, Emergency), computed from "
    "storage with the official State Index formula [4] (49%, 23%, 13% and 15% of months for Alarcón-Contreras), "
    "and the *transfer level* (1-4) under RD 638/2021 (since 2014: 15, 55, 58 and 17 months).",
    "**O3, clustering:** group the 114 reservoirs by the shape of their series (seasonal share, yearly cycle, "
    "drought response, recovery speed) with k-means or hierarchical clustering.",
])
para("**Hypotheses.** **H1:** hyperannual reservoirs are poorly predicted by a model that only looks back 12 months "
     "or less. **H2:** long-memory features improve 3-6-month forecasts for these reservoirs. **H3:** forecasting "
     "storage and then applying the official rules predicts the drought state and transfer level better than "
     "classifying the state directly. **H4:** reservoirs form distinct groups (seasonal vs. hyperannual) that need "
     "different models.", indent=False, before=3)
para("**Evaluation.** Time-based split: training 1988-2016, validation 2017-2020, test 2021-2026 (including the "
     "2022-24 drought and the period after the 2021 rule change); no random splits. Baselines: persistence, monthly "
     "climatology, historical analogues and the Baron et al. feature set. Metrics: NSE, RMSE and bias for storage; "
     "macro-F1 and recall of the severe classes for states; silhouette and skill per cluster for O3. Testing only on "
     "unseen periods also answers the critique that learning from the past is risky when conditions change [4].")
figure("acm_fig2_seasonal.png", COL_W, "Figure 2: Typical yearly cycle per basin: median and middle 50% of "
       "years. Year-to-year differences are larger than the seasonal cycle.")

h1("5 Data Enrichment")
para("Storage data show *what* happens but not *why*. Table 3 lists the public datasets we will join, all at "
     "monthly resolution.", indent=False)
table("Table 3: Public datasets for enrichment.", [
    ["Dataset (source)", "Variables", "Use"],
    ["AEMET OpenData (free API key)", "Station rainfall and temperature", "Accumulated rainfall, SPI/SPEI"],
    ["Copernicus ERA5", "Gridded rainfall, temperature, snow", "Catchment averages, snow"],
    ["SAIH Tajo / CEDEX", "Reservoir inflows and outflows", "12-month inflow (transfer level 1)"],
    ["MITECO drought reports", "Official monthly scarcity indices", "Validate drought states"],
    ["Transfer orders (BOE)", "Declared level and volume", "Ground truth for transfer level"],
    ["NOAA; Univ. of Barcelona", "NAO and WeMO indices", "Long-range rainfall predictors"],
    ["INE; ESYRCE; REE", "Population, irrigation, hydropower", "Demand and release proxies"],
], [1.15, 1.15, 1.03], size=7.5)

h1("6 Feasibility Study")
para("**Data.** The main dataset is open, already downloaded, converted and explored. The study area provides about "
     "50,000 reservoir-months, more than three times the training data of Baron et al. [1]. All enrichment sources "
     "are free: AEMET and Copernicus require only a free registration, and the other sources are public downloads or "
     "official publications.", indent=False)
para("**Technical.** The data are small (under 100 MB), so a laptop is enough. We use Python (pandas, scikit-learn, "
     "XGBoost/LightGBM) and BigML from the course tools to compare results, with all code in the team’s GitHub "
     "repository. The methods (regression, classification and clustering) are part of the course contents.")
para("**Risks.** Table 4 lists the main risks and how we will handle them.")
table("Table 4: Main risks and mitigations.", [
    ["Risk", "Mitigation"],
    ["Inflow data not available", "Storage-only transfer rule, checked against levels declared in the BOE"],
    ["Few severe droughts in the test period", "Macro-F1, class weights, rolling-origin evaluation"],
    ["Matching weather to catchments takes time", "Start with ERA5 basin averages, add stations later"],
    ["Hyperannual reservoirs stay hard to predict", "Report skill relative to baselines; a negative H2 is still a result"],
    ["Rule changes (2014, 2021)", "Apply current rules to the whole history as a storage-based label"],
], [1.45, 1.88])
para("**Timeline.** Until Deliverable 2 (27 November): download the enrichment data, clean, aggregate to months, "
     "build features and complete the exploration. Until the final deliverable (16 December): train and evaluate the "
     "models, cluster the reservoirs, and write the final report and presentation.", indent=False)
para("**Conclusion.** The data are available, the computing needs are small and the methods are covered by the "
     "course, so the project is feasible within the semester.")

h1("References")
refs = [
    "H. E. Baron, N. J. Rickards, R. Chengot, and V. J. D. Keller. 2026. Subseasonal to seasonal prediction and "
    "forecasting of reservoir storage using a machine learning model in the UK, Spain and France. *International "
    "Journal of River Basin Management*. https://doi.org/10.1080/15715124.2026.2729476",
    "O. García-Feal, J. González-Cao, D. Fernández-Nóvoa, G. Astray Dopazo, and M. Gómez-Gesteira. 2022. Comparison "
    "of machine learning techniques for reservoir outflow forecasting. *Natural Hazards and Earth System Sciences* "
    "22, 3859-3874. https://doi.org/10.5194/nhess-22-3859-2022",
    "S. Güneş Şen. 2025. Machine learning-based water level forecast in a dam reservoir: a case study of Karaçomak "
    "Dam, Türkiye. *Sustainability* 17, 18. https://doi.org/10.3390/su17188378",
    "D. Haro-Monteagudo, A. Solera, and J. Andreu. 2017. Drought early warning based on optimal risk forecasts in "
    "regulated river systems: application to the Jucar River Basin (Spain). *Journal of Hydrology* 544, 36-45. "
    "https://doi.org/10.1016/j.jhydrol.2016.11.022",
    "D. Jiménez Cando. 2025. *Predicción estacional de los indicadores de sequía prolongada en la Demarcación "
    "Hidrográfica del Júcar*. Master’s thesis. Universitat Politècnica de València.",
    "J. Lorenzo-Lacruz, S. M. Vicente-Serrano, J. I. López-Moreno, S. Beguería, J. M. García-Ruiz, and J. M. "
    "Cuadrat. 2010. The impact of droughts and water management on various hydrological systems in the headwaters "
    "of the Tagus River (central Spain). *Journal of Hydrology* 386, 13-26. "
    "https://doi.org/10.1016/j.jhydrol.2010.01.001",
    "Ministerio para la Transición Ecológica y el Reto Demográfico. 2026. *Base de datos del Boletín Hidrológico "
    "(BD-Embalses)*. Dataset.",
    "F. Pellicer-Martínez and J. M. Martínez-Paz. 2018. Climate change effects on the hydrology of the headwaters of "
    "the Tagus River: implications for the management of the Tagus-Segura transfer. *Hydrology and Earth System "
    "Sciences* 22, 6473-6491. https://doi.org/10.5194/hess-22-6473-2018",
    "M. M. Rao et al. 2026. Reassessing model complexity in reservoir outflow forecasting: a multi-site, "
    "physics-informed benchmark of deep learning and ensemble methods. *Ecological Engineering & Environmental "
    "Technology* 27, 3, 239-252.",
    "Real Decreto 638/2021, de 27 de julio, por el que se modifica el Real Decreto 773/2014 (reglas de explotación "
    "del trasvase Tajo-Segura). *Boletín Oficial del Estado*.",
    "J. Senent-Aparicio et al. 2021. A modelling approach to forecast the effect of climate change on the "
    "Tagus-Segura interbasin water transfer. *Water Resources Management* 35. "
    "https://doi.org/10.1007/s11269-021-02919-y",
    "H. Torelló-Sentelles and C. L. E. Franzke. 2022. Drought impact links to meteorological drought indicators and "
    "predictability in Spain. *Hydrology and Earth System Sciences* 26, 1821-1844. "
    "https://doi.org/10.5194/hess-26-1821-2022",
    "S. M. Vicente-Serrano and J. I. López-Moreno. 2005. Hydrological response to different time scales of "
    "climatological drought: an evaluation of the Standardized Precipitation Index in a mountainous Mediterranean "
    "basin. *Hydrology and Earth System Sciences* 9, 523-533. https://doi.org/10.5194/hess-9-523-2005",
]
for i, r in enumerate(refs, 1):
    p = doc.add_paragraph()
    add_runs(p, f"[{i}] {r}", size=7.5)
    pf = p.paragraph_format
    pf.left_indent, pf.first_line_indent = Inches(0.22), Inches(-0.22)
    pf.space_after = Pt(1.5)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT

doc.save(OUT)
print("saved", OUT)
