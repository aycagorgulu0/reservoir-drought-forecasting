"""Reusable feature functions for monthly reservoir series (used by step 31 and Deliverable 3).

All functions work on a table with one row per series and month, sorted by series then
month, on a complete monthly calendar (step 11 guarantees this), so a shift of k rows
within a series is exactly k months.
"""
import numpy as np
import pandas as pd


def lags(df, col, ks, by="reservoir"):
    """Value k months earlier: {col}_lag{k}."""
    g = df.groupby(by)[col]
    return pd.DataFrame({f"{col}_lag{k}": g.shift(k) for k in ks}, index=df.index)


def diffs(df, col, ks, by="reservoir"):
    """Change over the last k months: {col}_diff{k} = x(t) - x(t-k)."""
    g = df.groupby(by)[col]
    return pd.DataFrame({f"{col}_diff{k}": df[col] - g.shift(k) for k in ks}, index=df.index)


def rolling_means(df, col, windows, by="reservoir", min_frac=0.8):
    """Mean over the last w months including the current one: {col}_mean{w}."""
    out = {}
    for w in windows:
        out[f"{col}_mean{w}"] = (df.groupby(by)[col]
                                 .transform(lambda s: s.rolling(w, min_periods=int(w * min_frac)).mean()))
    return pd.DataFrame(out, index=df.index)


def rolling_std(df, col, w, by="reservoir", min_frac=0.8):
    return (df.groupby(by)[col]
            .transform(lambda s: s.rolling(w, min_periods=int(w * min_frac)).std())
            .rename(f"{col}_std{w}"))


def leads(df, col, hs, by="reservoir"):
    """Targets: value h months ahead, {col}_h{h} = x(t + h)."""
    g = df.groupby(by)[col]
    return pd.DataFrame({f"{col}_h{h}": g.shift(-h) for h in hs}, index=df.index)


def month_cycle(month_num):
    """Month encoded on a circle, so December and January are neighbours."""
    angle = 2 * np.pi * (np.asarray(month_num) - 1) / 12
    return pd.DataFrame({"month_sin": np.sin(angle), "month_cos": np.cos(angle)})


def climatology(train, col, by="reservoir", month_col="month_num"):
    """Average value per series and calendar month, from the training rows only."""
    return (train.groupby([by, month_col])[col].mean()
            .rename(f"{col}_clim").reset_index())


def seasonal_share(train, col, by="reservoir", month_col="month_num", min_months=120):
    """Share of a series' variance explained by its average yearly cycle (training rows only).

    Near 1: storage follows the same yearly cycle every year (seasonal reservoir).
    Near 0: storage changes mostly between years (hyperannual reservoir).
    """
    out = {}
    for name, g in train.dropna(subset=[col]).groupby(by):
        if len(g) < min_months:
            continue
        clim = g.groupby(month_col)[col].transform("mean")
        total = g[col].var()
        out[name] = clim.var() / total if total > 0 else np.nan
    return pd.Series(out, name="seasonal_share").rename_axis(by).reset_index()
