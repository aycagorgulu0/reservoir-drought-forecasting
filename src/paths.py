"""Project paths, shared by every script in src/.

All paths are built from this file's location, so scripts work from any
working directory (e.g. `python src/02_basic_stats.py` from the repo root).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA = ROOT / "data"
RAW = DATA / "raw"              # original downloads, never edited (not in git)
INTERIM = DATA / "interim"      # converted / cleaned intermediate files (not in git)
PROCESSED = DATA / "processed"  # final modelling tables

FIGURES = ROOT / "figures"
REPORTS = ROOT / "reports"

D2_TABLES = REPORTS / "deliverable_2" / "tables"  # small tables quoted in the Deliverable 2 report

MDB = RAW / "BD-Embalses.mdb"
WEEKLY_CSV = INTERIM / "reservoirs_spain_weekly.csv"          # 01: all of Spain, as converted
WEEKLY_CLEAN_CSV = INTERIM / "reservoirs_weekly_clean.csv"    # 10: study area, cleaned
MONTHLY_CSV = INTERIM / "reservoirs_monthly.csv"              # 11: monthly series + systems
RESERVOIRS_CSV = PROCESSED / "reservoirs.csv"                 # 10: one row per reservoir (metadata)

for _d in (RAW, INTERIM, PROCESSED, FIGURES, D2_TABLES):
    _d.mkdir(parents=True, exist_ok=True)
