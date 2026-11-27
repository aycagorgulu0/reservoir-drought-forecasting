"""Step 22 (integration): monthly NAO and WeMO climate indices.

Input : NOAA CPC monthly NAO index (text file)
        NCEP-NCAR reanalysis monthly sea-level pressure at Padua and San Fernando
        (IRI Data Library), all downloaded once to data/raw/indices/
Output: data/processed/climate_indices.csv   month, nao, wemo

NAO  North Atlantic Oscillation, as published by NOAA.
WeMO Western Mediterranean Oscillation index (Martin-Vide & Lopez-Bustins 2006):
     standardised sea-level pressure at San Fernando, Cádiz (36.28N, 6.21W) minus standardised
     pressure at Padua (45.40N, 11.48E). Negative phase (low pressure over the Gulf of Cádiz)
     brings rain to eastern Iberia. The University of Barcelona site that publishes it
     was unavailable (HTTP 500), so it is computed here from reanalysis pressure at the
     nearest 2.5-degree grid points. Pressures are standardised per calendar month with the
     1981-2016 mean and standard deviation (training years).
"""
import urllib.request

import numpy as np
import pandas as pd
from scipy.io import netcdf_file

from paths import CLIMATE_CSV, INDICES_DIR

NAO_URL = "https://www.cpc.ncep.noaa.gov/products/precip/CWlink/pna/norm.nao.monthly.b5001.current.ascii"
SLP_URL = ("https://iridl.ldeo.columbia.edu/SOURCES/.NOAA/.NCEP-NCAR/.CDAS-1/.MONTHLY/.Intrinsic/.MSL/"
           ".pressure/X/({lon})/VALUES/Y/({lat})/VALUES/T/(Jan%201950)/last/RANGE/data.nc")
STATIONS = {"padua": ("11.48E", "45.40N"), "san_fernando": ("6.21W", "36.28N")}
START, FIT_START, FIT_END = "1981-01-01", "1981-01-01", "2016-12-01"

INDICES_DIR.mkdir(parents=True, exist_ok=True)


def download(url, path):
    if not path.exists():
        print(f"Downloading {path.name} ...")
        urllib.request.urlretrieve(url, path)
    return path


# NAO
nao_file = download(NAO_URL, INDICES_DIR / "nao_monthly.txt")
nao = pd.read_csv(nao_file, sep=r"\s+", header=None, names=["year", "m", "nao"])
nao["month"] = pd.to_datetime(dict(year=nao["year"], month=nao["m"], day=1))
nao = nao.set_index("month")["nao"]

# WeMO from sea-level pressure
slp = {}
for name, (lon, lat) in STATIONS.items():
    f = download(SLP_URL.format(lon=lon, lat=lat), INDICES_DIR / f"slp_{name}.nc")
    with netcdf_file(f, "r", mmap=False) as nc:
        t = nc.variables["T"][:].astype(float)
        p = nc.variables["pressure"][:].astype(float).ravel()
        t_units = nc.variables["T"].units.decode()
        grid = (float(nc.variables["X"][:].ravel()[0]), float(nc.variables["Y"][:].ravel()[0]))
    assert "months since 1960-01-01" in t_units, t_units
    idx = pd.to_datetime([f"{1960 + int(np.floor(v)) // 12}-{int(np.floor(v)) % 12 + 1:02d}-01" for v in t])
    slp[name] = pd.Series(p, index=idx)
    print(f"  {name}: grid point lon {grid[0]}, lat {grid[1]}, {len(p)} months")
slp = pd.DataFrame(slp)

fit = slp.loc[FIT_START:FIT_END]
clim = fit.groupby(fit.index.month).agg(["mean", "std"])
z = pd.DataFrame(index=slp.index)
for name in STATIONS:
    mu = slp.index.month.map(clim[(name, "mean")])
    sd = slp.index.month.map(clim[(name, "std")])
    z[name] = (slp[name] - mu.to_numpy()) / sd.to_numpy()
wemo = (z["san_fernando"] - z["padua"]).rename("wemo")

out = pd.concat([nao, wemo], axis=1).loc[START:].dropna(how="all")
out.index.name = "month"
out = out.reset_index()
out["month"] = out["month"].dt.strftime("%Y-%m-%d")
out.to_csv(CLIMATE_CSV, index=False, float_format="%.4f")
print(f"Saved {CLIMATE_CSV.name}: {len(out)} months ({out['month'].iloc[0]} - {out['month'].iloc[-1]}), "
      f"missing NAO {out['nao'].isna().sum()}, missing WeMO {out['wemo'].isna().sum()}")
print(out[["nao", "wemo"]].describe().loc[["mean", "std", "min", "max"]].round(2).to_string())
