# Forecasting Reservoir Storage and Drought States in the Tajo, Guadiana and Júcar Basins

Data Mining course project (Minería de Datos, Universidad de Castilla-La Mancha, 2026), following the KDD process.

**Team:** Ayça Görgülü, Mina Özdoğan, Beyza Nur Balota

## Problem

Spain's official drought indicators only describe the *current* situation. This project uses data mining to **predict** reservoir storage and the official drought and Tajo-Segura transfer states several months ahead, for the 114 reservoirs of the Tajo, Guadiana and Júcar basins. The key reservoirs are Entrepeñas, Buendía, Alarcón and Contreras.

- **O1, regression:** forecast monthly % full 1, 3 and 6 months ahead.
- **O2, classification:** predict the drought state (Normal / Pre-alert / Alert / Emergency) and the transfer level (1-4).
- **O3, clustering:** group reservoirs by behaviour (seasonal vs. hyperannual).

These reservoirs are *hyperannual*: storage changes much more between years than within a year. The closest published model (Baron et al. 2026) performs poorly on this kind of reservoir. See [docs/PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md) for details and [docs/literature_review.md](docs/literature_review.md) for related work.

## Repository structure

```
├── data/
│   ├── raw/          original downloads, never edited (not in git, see data/README.md)
│   ├── interim/      converted and cleaned intermediate files (not in git)
│   └── processed/    final modelling tables
├── src/              pipeline scripts, numbered in the order they run
│   └── paths.py      shared paths used by every script
├── figures/          figures produced by the scripts
├── reports/
│   ├── deliverable_1/  problem definition (PDF + script that generated its first draft)
│   └── deliverable_2/  data selection, preprocessing and transformation
├── docs/             project summary and literature review
└── requirements.txt
```

## Setup

Requires Python 3.11.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
```

Reading the original `.mdb` file needs the **Microsoft Access ODBC driver** (Windows, "Microsoft Access Database Engine 2016 Redistributable"). It is only needed for step 01.

## Getting the data

The raw data is not stored in this repository because it is too large for GitHub. See [data/README.md](data/README.md) for how to download it.

## Running the pipeline

Run the scripts from the repository root, in order:

| Step | Script | Output |
|---|---|---|
| 00 | `python src/00_inspect_mdb.py` | Prints tables, columns and sample rows of the Access database |
| 01 | `python src/01_convert_to_csv.py` | `data/interim/reservoirs_spain_weekly.csv` (English column names, numeric values, `pct_full`) |
| 02 | `python src/02_basic_stats.py` | Prints dataset statistics |
| 03 | `python src/03_make_plots.py` | Exploratory figures `figures/fig1-5_*.png` |
| 04 | `python src/04_make_acm_figures.py` | Column-width figures for the ACM reports |

## Data sources

| Source | Use | License |
|---|---|---|
| MITECO, *Base de datos del Boletín Hidrológico* (BD-Embalses) | Weekly reservoir storage, 1988-2026 | Open data, Spanish Government |

More sources (CHIRPS rainfall, NAO and WeMO climate indices) will be added in Deliverable 2.

## Deliverables

| Deliverable | Due | Files |
|---|---|---|
| 1. Problem definition | 30 Oct 2026 | [reports/deliverable_1/Deliverable1.pdf](reports/deliverable_1/Deliverable1.pdf) |
| 2. Data selection, preprocessing and transformation | 27 Nov 2026 | `reports/deliverable_2/` |
| 3. Modelling and results | 16 Dec 2026 | |
