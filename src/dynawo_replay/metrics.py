import numpy as np
import pandas as pd
from pydantic import BaseModel
from sklearn.metrics import r2_score


class ComparisonMetrics(BaseModel):
    rmse: float
    nrmse: float
    mae: float
    r2: float


def align_to_common_index(s1: pd.Series, s2: pd.Series) -> tuple[pd.Series, pd.Series]:
    """
    Combines two pd.Series into a common index (union of indices) and interpolates missing values.
    """
    s1 = s1[~s1.index.duplicated()]
    s2 = s2[~s2.index.duplicated()]
    common_index = s1.index.union(s2.index)
    s1 = s1.reindex(common_index).interpolate()
    s2 = s2.reindex(common_index).interpolate()
    return s1, s2


def compare_curves(s1: pd.Series, s2: pd.Series) -> ComparisonMetrics:
    """
    Return comparison metrics between the given two curves
    """
    s1, s2 = align_to_common_index(s1, s2)
    s1_range = np.ptp(s1)
    rmse = ((s1 - s2) ** 2).mean() ** 0.5
    return ComparisonMetrics(
        rmse=rmse,
        nrmse=rmse / s1_range if s1_range else np.nan,
        mae=abs(s1 - s2).mean(),
        r2=r2_score(s1, s2),
    )
