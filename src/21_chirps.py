"""Step 21 (integration): monthly CHIRPS rainfall per catchment, and SPI.

Input : CHIRPS v2.0 monthly, 0.05 deg (downloaded once to data/raw/chirps/, Spain box only,
        through the IRI Data Library, which cuts the global grid on the server)
        data/interim/catchments.geojson (step 20)
Output: data/processed/rainfall_monthly.csv   catchment_id, month, precip_mm, spi_3 ... spi_36
        reports/deliverable_2/tables/rainfall_summary.csv

Catchment rainfall = mean of the grid cells whose centre lies inside the catchment,
weighted by cos(latitude) (cell area).

SPI (McKee et al. 1993): rainfall summed over k months, fitted per calendar month with a
gamma distribution (plus the probability of a zero total), then converted to a standard
normal value. The fit uses only 1981-2016 (training years), so the test period does not
leak into the features. SPI 0 = normal, below -1 = dry, below -2 = extremely dry.
"""
import json
import urllib.request

import numpy as np
import pandas as pd
from matplotlib.path import Path as MplPath
from scipy import stats
from scipy.io import netcdf_file

from paths import CATCHMENT_SHAPES, CHIRPS_NC, D2_TABLES, RAINFALL_CSV
from study_area import TRAIN_END

LON, LAT = (-7.6, 1.3), (37.9, 43.4)   # box around all catchments
URL = ("https://iridl.ldeo.columbia.edu/SOURCES/.UCSB/.CHIRPS/.v2p0/.monthly/.global/.precipitation/"
       f"X/{LON[0]}/{LON[1]}/RANGEEDGES/Y/{LAT[0]}/{LAT[1]}/RANGEEDGES/data.nc")
SPI_WINDOWS = [3, 6, 12, 24, 36]
FIT_END = pd.Timestamp(TRAIN_END)   # SPI fitted on the training years only

# 1. Download once
if not CHIRPS_NC.exists():
    CHIRPS_NC.parent.mkdir(parents=True, exist_ok=True)
    print("Downloading CHIRPS monthly for the Spain box (about 40 MB) ...")
    urllib.request.urlretrieve(URL, CHIRPS_NC)

with netcdf_file(CHIRPS_NC, "r", mmap=False) as nc:
    lon = nc.variables["X"][:].astype(float)
    lat = nc.variables["Y"][:].astype(float)
    t = nc.variables["T"][:].astype(float)
    pvar = nc.variables["precipitation"]
    precip = pvar[:].astype(float)            # (T, Y, X)
    units = pvar.units.decode() if hasattr(pvar, "units") else "?"
    fill = getattr(pvar, "missing_value", None)
    t_units = nc.variables["T"].units.decode()
if fill is not None:
    precip[precip == float(fill)] = np.nan
precip[precip < 0] = np.nan
# IRI time axis: months since 1960-01-01 (mid-month values such as 252.5)
assert "months since 1960-01-01" in t_units, t_units
months = pd.to_datetime([f"{1960 + int(np.floor(v)) // 12}-{int(np.floor(v)) % 12 + 1:02d}-01" for v in t])
print(f"CHIRPS grid: {len(lat)} x {len(lon)} cells, {len(months)} months "
      f"({months[0]:%b %Y} - {months[-1]:%b %Y}), units {units}")

# 2. Catchment means
glon, glat = np.meshgrid(lon, lat)
centres = np.column_stack([glon.ravel(), glat.ravel()])
weights = np.cos(np.radians(glat)).ravel()
flat = precip.reshape(len(months), -1)

rows = []
for f in json.loads(CATCHMENT_SHAPES.read_text())["features"]:
    cid = f["properties"]["catchment_id"]
    inside = np.zeros(len(centres), bool)
    for poly in f["geometry"]["coordinates"]:
        inside |= MplPath(np.array(poly[0])).contains_points(centres)
    w = weights[inside]
    vals = flat[:, inside]
    ok = ~np.isnan(vals)
    mean = (np.where(ok, vals, 0) * w).sum(axis=1) / (ok * w).sum(axis=1)
    rows.append(pd.DataFrame({"catchment_id": cid, "month": months, "precip_mm": mean}))
    print(f"  {cid:<11} {inside.sum():>5} cells, mean {12 * np.nanmean(mean):.0f} mm/year")
rain = pd.concat(rows, ignore_index=True)


# 3. SPI
def spi(series_sum, month_num, dates):
    out = np.full(len(series_sum), np.nan)
    for m in range(1, 13):
        sel = month_num == m
        fit = series_sum[sel & (dates <= FIT_END)]
        fit = fit[~np.isnan(fit)]
        if len(fit) < 20:
            continue
        q = np.mean(fit == 0)
        pos = fit[fit > 0]
        a, loc, scale = stats.gamma.fit(pos, floc=0)
        x = series_sum[sel]
        cdf = q + (1 - q) * stats.gamma.cdf(x, a, loc=0, scale=scale)
        cdf = np.clip(cdf, 1e-6, 1 - 1e-6)
        out[sel] = np.where(np.isnan(x), np.nan, stats.norm.ppf(cdf))
    return out


rain = rain.sort_values(["catchment_id", "month"]).reset_index(drop=True)
for k in SPI_WINDOWS:
    sums = rain.groupby("catchment_id")["precip_mm"].transform(lambda s: s.rolling(k, min_periods=k).sum())
    rain[f"spi_{k}"] = np.nan
    for cid, idx in rain.groupby("catchment_id").groups.items():
        rain.loc[idx, f"spi_{k}"] = spi(sums.loc[idx].to_numpy(), rain.loc[idx, "month"].dt.month.to_numpy(),
                                         rain.loc[idx, "month"].to_numpy())

rain["month"] = rain["month"].dt.strftime("%Y-%m-%d")
rain.to_csv(RAINFALL_CSV, index=False, float_format="%.3f")
print(f"\nSaved {RAINFALL_CSV.name}: {len(rain):,} rows, {rain['catchment_id'].nunique()} catchments")

# 4. Summary for the report
r = rain.assign(month=pd.to_datetime(rain["month"]))
summary = (r.groupby("catchment_id")
           .agg(first=("month", "min"), last=("month", "max"), months=("month", "size"),
                mean_mm_year=("precip_mm", lambda s: round(12 * s.mean())),
                driest_12m_spi=("spi_12", "min"))
           .reset_index())
summary["driest_12m_spi"] = summary["driest_12m_spi"].round(2)
summary["driest_12m_month"] = [r.loc[r.loc[r["catchment_id"] == c, "spi_12"].idxmin(), "month"].strftime("%b %Y")
                               for c in summary["catchment_id"]]
summary.to_csv(D2_TABLES / "rainfall_summary.csv", index=False)
print(summary.to_string(index=False))
