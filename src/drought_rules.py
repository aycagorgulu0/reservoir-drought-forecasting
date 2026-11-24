"""Official Spanish drought and transfer rules, written once and reused by steps 30+ and Deliverable 3.

1. State Index (Índice de Estado, CHJ 2007; Haro-Monteagudo et al. 2017)
   For a volume V in a given calendar month, with V_min, V_avg, V_max the historical
   minimum, mean and maximum for that calendar month:
       V >= V_avg:  SI = 1/2 * (1 + (V - V_avg) / (V_max - V_avg))
       V <  V_avg:  SI = 1/2 * (V - V_min) / (V_avg - V_min)
   Scenarios: Normal SI >= 0.5, Pre-alert 0.3-0.5, Alert 0.15-0.3, Emergency < 0.15.
   The official basin index also uses rainfall, river flow and groundwater; ours uses
   reservoir storage only (about 50% of the Júcar index).

2. Tajo-Segura transfer levels (RD 773/2014, amended by RD 638/2021)
   Based on Entrepeñas + Buendía storage at the start of each month:
       Level 1: storage >= 1,300 hm3  (or 12-month inflow >= 1,400 hm3: no inflow data yet)
       Level 4: storage < 400 hm3
       Level 3: storage <= that month's threshold (586-688 hm3)
       Level 2: otherwise
"""
import numpy as np
import pandas as pd

STATES = ["Normal", "Pre-alert", "Alert", "Emergency"]  # code 0..3, 3 = most severe
SI_BOUNDS = [0.5, 0.3, 0.15]                            # lower bound of Normal, Pre-alert, Alert

TRANSFER_LEVEL1_HM3 = 1300
TRANSFER_LEVEL4_HM3 = 400
TRANSFER_LEVEL3_THRESHOLD_HM3 = {  # calendar month -> level 3 threshold (RD 638/2021)
    10: 613, 11: 609, 12: 605, 1: 602, 2: 597, 3: 591,
    4: 586, 5: 645, 6: 673, 7: 688, 8: 661, 9: 631,
}
TRANSFER_MONTHLY_HM3 = {1: 60, 2: 27, 3: 20, 4: 0}  # volume per level (level 3: up to 20)


def si_reference(df, value_col, month_col="month_num", by="reservoir", min_years=10):
    """Historical min, mean and max per series and calendar month.

    Pass only the reference (training) rows. Calendar months with fewer than
    `min_years` values get no reference, so their SI stays missing.
    """
    ref = (df.dropna(subset=[value_col])
           .groupby([by, month_col])[value_col]
           .agg(v_min="min", v_avg="mean", v_max="max", n_years="count")
           .reset_index())
    return ref[ref["n_years"] >= min_years]


def state_index(v, v_min, v_avg, v_max):
    """State Index in [0, 1]. Values beyond the reference extremes are clipped."""
    v, v_min, v_avg, v_max = (np.asarray(a, dtype=float) for a in (v, v_min, v_avg, v_max))
    with np.errstate(divide="ignore", invalid="ignore"):
        above = 0.5 * (1 + (v - v_avg) / (v_max - v_avg))
        below = 0.5 * (v - v_min) / (v_avg - v_min)
    si = np.where(v >= v_avg, above, below)
    return np.clip(si, 0, 1)


def drought_state(si):
    """State Index -> state code 0 Normal, 1 Pre-alert, 2 Alert, 3 Emergency (NaN stays NaN)."""
    si = np.asarray(si, dtype=float)
    code = np.select([si >= SI_BOUNDS[0], si >= SI_BOUNDS[1], si >= SI_BOUNDS[2]], [0, 1, 2], default=3)
    return np.where(np.isnan(si), np.nan, code)


def transfer_level(storage_hm3, month_num):
    """Transfer level 1-4 from start-of-month Entrepeñas + Buendía storage (storage rule only)."""
    s = np.asarray(storage_hm3, dtype=float)
    threshold = pd.Series(month_num).map(TRANSFER_LEVEL3_THRESHOLD_HM3).to_numpy(dtype=float)
    level = np.select([s >= TRANSFER_LEVEL1_HM3, s < TRANSFER_LEVEL4_HM3, s <= threshold],
                      [1, 4, 3], default=2)
    return np.where(np.isnan(s), np.nan, level)
