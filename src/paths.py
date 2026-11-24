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

MDB = RAW / "BD-Embalses.mdb"
WEEKLY_CSV = INTERIM / "reservoirs_spain_weekly.csv"

for _d in (RAW, INTERIM, PROCESSED, FIGURES):
    _d.mkdir(parents=True, exist_ok=True)
