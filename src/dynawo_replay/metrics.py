from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score

from .exceptions import NotStabilizedCurve
from .utils import drop_duplicated_index


@dataclass
class ComparisonMetrics:
    ptp_diff: float
    ss_value_diff: float
    ss_time_diff: float
    ptp_diff_rel: float
    ss_value_diff_rel: float
    r2: float
    rmse: float
    nrmse: float
    mae: float


def align_to_common_index(s1: pd.Series, s2: pd.Series) -> tuple[pd.Series, pd.Series]:
    """
    Combines two pd.Series into a common index (union of indices) and interpolates missing values.
    """
    s1 = drop_duplicated_index(s1)
    s2 = drop_duplicated_index(s2)
    common_index = s1.index.union(s2.index)
    s1 = s1.reindex(common_index).interpolate()
    s2 = s2.reindex(common_index).interpolate()
    return s1, s2


def get_stabilization_metrics(s: pd.Series, min_steady_interval=5, steady_tol=0.002):
    """
    Returns the final steady value and the stabilization time.
    Raises NotStabilizedCurve if the curve does not finish stable, that is,
    its values exceed steady_tol in the last min_steady_interval of the curve.
    The steady_tol is considered a relative value if the steady_state_value
    of the curve is higher than 1.
    """
    steady_state_value = s.iloc[-1]
    if abs(steady_state_value) <= 1:
        ss_upper_bound = steady_state_value + steady_tol
        ss_lower_bound = steady_state_value - steady_tol
    else:
        ss_upper_bound = steady_state_value * (1 + steady_tol)
        ss_lower_bound = steady_state_value * (1 - steady_tol)
    last_interval = s[s.index >= s.index.max() - min_steady_interval]
    if not last_interval.between(ss_lower_bound, ss_upper_bound).all():
        raise NotStabilizedCurve()
    stabilization_time = s[~s.between(ss_lower_bound, ss_upper_bound)].index.max()
    return steady_state_value, stabilization_time


def compare_curves(s1: pd.Series, s2: pd.Series) -> ComparisonMetrics:
    """
    Return comparison metrics between the given two curves
    """
    s1, s2 = align_to_common_index(s1, s2)
    s1_range = np.ptp(s1)
    rmse = ((s1 - s2) ** 2).mean() ** 0.5
    ptp1, ptp2 = np.ptp(s1), np.ptp(s2)
    ptp_diff = abs(ptp1 - ptp2)
    try:
        ss_value1, ss_time1 = get_stabilization_metrics(s1)
        ss_value2, ss_time2 = get_stabilization_metrics(s2)
        ss_value_diff = abs(ss_value1 - ss_value2)
        ss_time_diff = abs(ss_time1 - ss_time2)
    except NotStabilizedCurve:
        ss_value1, ss_time1 = np.nan, np.nan
        ss_value2, ss_time2 = np.nan, np.nan
        ss_value_diff = np.nan
        ss_time_diff = np.nan
    return ComparisonMetrics(
        ptp_diff=ptp_diff,
        ss_value_diff=ss_value_diff,
        ss_time_diff=ss_time_diff,
        ptp_diff_rel=ptp_diff / ptp1 if ptp1 else np.nan,
        ss_value_diff_rel=ss_value_diff / ss_value1 if ss_value1 else np.nan,
        r2=r2_score(s1, s2),
        rmse=rmse,
        nrmse=rmse / s1_range if s1_range else np.nan,
        mae=abs(s1 - s2).mean(),
    )
