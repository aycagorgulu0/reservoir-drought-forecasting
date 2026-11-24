"""Convert BD-Embalses.mdb to a clean CSV with English column names and numeric values."""

import pandas as pd
import pyodbc

from paths import MDB, WEEKLY_CSV as OUT

COLUMNS = {
    "AMBITO_NOMBRE": "basin",
    "EMBALSE_NOMBRE": "reservoir",
    "FECHA": "date",
    "AGUA_TOTAL": "capacity_hm3",
    "AGUA_ACTUAL": "stored_hm3",
    "ELECTRICO_FLAG": "hydro_flag",
}

conn = pyodbc.connect(
    r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + str(MDB) + ";"
)
table = [t.table_name for t in conn.cursor().tables(tableType="TABLE")][0]
df = pd.read_sql(f"SELECT * FROM [{table}]", conn).rename(columns=COLUMNS)

# Values are stored as text with Spanish formatting ("1.234,56")
for col in ["capacity_hm3", "stored_hm3"]:
    df[col] = pd.to_numeric(
        df[col].astype(str).str.strip()
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce",
    )
df["hydro_flag"] = df["hydro_flag"].astype("Int64")
df["date"] = pd.to_datetime(df["date"])
df["basin"] = df["basin"].str.strip()
df["reservoir"] = df["reservoir"].str.strip()
df["pct_full"] = (100 * df["stored_hm3"] / df["capacity_hm3"]).round(2)

df = df.sort_values(["basin", "reservoir", "date"]).reset_index(drop=True)
OUT.parent.mkdir(exist_ok=True)
df.to_csv(OUT, index=False, encoding="utf-8")
print(f"Saved {len(df):,} rows to {OUT}")
print(df.head())
