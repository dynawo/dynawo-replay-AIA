import subprocess
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import pchip_interpolate

from .config import settings
from .exceptions import NotSupportedModel
from .lp_filters import apply_filtfilt, critically_damped_lpf
from .schemas.ddb import Model
from .schemas.ext_var import ExternalVariables, VariableType
from .schemas.io import parser
from .schemas.parameters import Parameter, ParametersSet


def find_jobs_file(case_folder: Path):
    return next(case_folder.glob("*.jobs"), None) or next(case_folder.glob("*JOB*"))


def list_available_vars(model, dynawo=settings.DYNAWO_HOME):
    model = parser.parse(dynawo / "ddb" / f"{model}.desc.xml", Model)
    return model.elements.variables.variable


def print_dynawo_version(dynawo_home=settings.DYNAWO_HOME):
    return subprocess.run(
        [dynawo_home / "dynawo.sh", "version"],
        capture_output=True,
        check=True,
        text=True,
    ).stdout


def inspect_model(model_name, dynawo_home=settings.DYNAWO_HOME):
    ddb_folder = dynawo_home / "ddb"
    model = parser.parse(ddb_folder / f"{model_name}.desc.xml", Model)
    external_vars = parser.parse(ddb_folder / f"{model_name}.extvar", ExternalVariables)
    return model, external_vars.variable


def inspect_model_extvars(model_name, dynawo_home=settings.DYNAWO_HOME):
    ddb_folder = dynawo_home / "ddb"
    external_vars = parser.parse(ddb_folder / f"{model_name}.extvar", ExternalVariables)
    return external_vars.variable


def drop_duplicated_index(s: pd.Series | pd.DataFrame):
    return s.loc[~s.index.duplicated()]


def reduce_curve(s: pd.Series):
    "Returns a reduced equivalent (by interpolation) version of the series"
    s = drop_duplicated_index(s)
    s_prima = s.diff() / s.index.to_series().diff()
    mask = (s_prima.diff() == 0) & (s_prima.diff(-1) == 0)
    s = s.loc[~mask]
    return s


def reindex(s: pd.Series, new_index: np.array, method="pchip") -> pd.Series:
    if method == "pchip":
        new_values = pchip_interpolate(s.index, s.values, new_index)
    elif method == "linear":
        new_values = np.interp(new_index, s.index, s.values)
    else:
        raise RuntimeError()
    return pd.Series(new_values, index=new_index)


def postprocess_curve(
    s: pd.Series,
    target_freq=settings.POSTPROCESS_TARGET_FREQ,
    intermediate_freq=settings.POSTPROCESS_FINE_FREQ,
):
    "Post-process a time series to remove high-frequency variations using resampling and low-pass filtering."
    t0, tf = s.index.min(), s.index.max()
    intermediate_time_grid = np.arange(t0, tf, step=1 / intermediate_freq)
    target_time_grid = np.arange(t0, tf, step=1 / target_freq)
    cutoff_freq = target_freq / 2
    s = drop_duplicated_index(s)
    if np.ptp(s) == 0:
        return pd.Series(s.iloc[0], index=target_time_grid)
    s = reindex(s, intermediate_time_grid)
    b, a = critically_damped_lpf(cutoff_freq, intermediate_freq)
    s = pd.Series(apply_filtfilt(b, a, s.values, padding_method="gust"), index=s.index)
    s = reindex(s, target_time_grid)
    return s


def combine_dataframes(dfs: list[pd.DataFrame]):
    "Combines many dataframe into one, interpolating missing values"
    combined_df = drop_duplicated_index(dfs[0])
    for df in dfs[1:]:
        combined_df = pd.merge(
            combined_df,
            drop_duplicated_index(df),
            left_index=True,
            right_index=True,
            how="outer",
        )
    combined_df = combined_df.sort_index().interpolate()
    return combined_df


def infer_core_connection_vars(
    lib: str, check_in_list: list[str] | None = None
) -> tuple[str, str, str]:
    """
    Infers the connection-related variable names based on the given library name.

    This function determines the voltage real and imaginary components (v_re, v_im)
    and the omega reference (omega_ref) associated with the model's connection to
    the network. The returned variables depend on the prefix derived from the
    library name, with special handling for specific cases like 'GeneratorSynchronous'.

    Args:
        lib (str): The name of the library/model to derive the connection variables from.

    Returns:
        tuple: A tuple containing the inferred voltage real (v_re), voltage imaginary
                (v_im), and omega reference (omega_ref) variable names.

    Raises:
        RuntimeError: If the library name does not match any expected prefix.
    """
    if lib.startswith("GeneratorSynchronous"):
        prefix = "generator"
    elif lib.startswith("IECWPP"):
        prefix = "WPP"
    elif lib.startswith("BESScb"):
        prefix = "BESScb"
    elif lib.startswith("WTG4A"):
        prefix = "WTG4A"
    elif lib.startswith("WTG4B"):
        prefix = "WTG4B"
    elif lib.startswith("Photovoltaics"):
        prefix = "photovoltaics"
    else:
        raise RuntimeError(f"Unexpected {lib=}")
    if "Aux" in lib:
        v_re = "coupling_terminal1_V_re"
        v_im = "coupling_terminal1_V_im"
    elif "Tfo" in lib:
        v_re = "transformer_terminal1_V_re"
        v_im = "transformer_terminal1_V_im"
    else:
        v_re = f"{prefix}_terminal_V_re"
        v_im = f"{prefix}_terminal_V_im"
    if lib.startswith("GeneratorSynchronous"):
        omega_ref = "generator_omegaRefPu_value"
        if lib == "GeneratorSynchronousFourWindingsTGov1Sexs":
            omega_ref = "governor_omegaRefPu"
    else:
        omega_ref = f"{prefix}_omegaRefPu"
    if check_in_list is not None:
        for v in (omega_ref, v_re, v_im):
            if v not in check_in_list:
                raise RuntimeError(f"Variable {v} not in the check_list")
    return omega_ref, v_re, v_im


@dataclass
class ConnectionVars:
    omegaRefPu: str
    terminal_V_re: str
    terminal_V_im: str
    extra: list[str]

    def all_vars(self):
        return [self.omegaRefPu, self.terminal_V_re, self.terminal_V_im, *self.extra]

    @classmethod
    def from_lib(cls, lib):
        try:
            ext_vars = inspect_model_extvars(lib)
        except Exception as e:
            raise NotSupportedModel("Cannot read extvar file") from e
        ext_var_names = [v.id.replace(".", "_") for v in ext_vars]
        try:
            omegaRefPu, terminal_V_re, terminal_V_im = infer_core_connection_vars(
                lib, check_in_list=ext_var_names
            )
        except RuntimeError as e:
            raise NotSupportedModel("Cannot infer core connection vars") from e
        extra = []
        for v in ext_vars:
            v_name = v.id.replace(".", "_")
            if v_name in (omegaRefPu, terminal_V_re, terminal_V_im):
                continue
            if v.optional or v.default_value:
                continue
            if v.type_value != VariableType.CONTINUOUS:
                raise NotSupportedModel(f"Mandatory non-continuous var {v_name}")
            extra.append(v_name)
        return cls(
            omegaRefPu=omegaRefPu,
            terminal_V_re=terminal_V_re,
            terminal_V_im=terminal_V_im,
            extra=extra,
        )

    @classmethod
    @cache
    def from_lib_or_none(cls, lib):
        try:
            return cls.from_lib(lib)
        except NotSupportedModel:
            return None


def solve_references(pset: ParametersSet, ref_value: dict):
    "Replaces all references in the parameters set using the ref_value dict given"
    for ref in pset.reference:
        pset.par.append(
            Parameter(
                name=ref.name,
                type_value=ref.type_value,
                value=ref_value[ref.name],
            )
        )
    pset.reference = []
    return pset


def to_polars(df, re_column, im_column):
    return (
        np.hypot(df[re_column], df[im_column]),
        np.arctan2(df[im_column], df[re_column]),
    )
