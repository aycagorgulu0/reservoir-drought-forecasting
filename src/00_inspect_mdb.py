"""List the tables and columns in BD-Embalses.mdb, with row counts and sample rows."""

import pyodbc

from paths import MDB
conn = pyodbc.connect(
    r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + str(MDB) + ";"
)
cur = conn.cursor()

tables = [t.table_name for t in cur.tables(tableType="TABLE")]
for table in tables:
    n = cur.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
    print(f"\n=== {table}  ({n:,} rows)")
    for col in cur.columns(table=table):
        print(f"   {col.column_name:<25} {col.type_name}")
    for row in cur.execute(f"SELECT TOP 3 * FROM [{table}]").fetchall():
        print("   ", tuple(row))
