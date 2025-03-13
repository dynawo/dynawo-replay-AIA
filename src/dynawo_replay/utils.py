import pandas as pd

from .config import settings
from .schemas.ddb import Model
from .schemas.io import parser
from .schemas.parameters import Parameter, ParametersSet


def list_available_vars(model, dynawo=settings.DYNAWO_HOME):
    model = parser.parse(dynawo / "ddb" / f"{model}.desc.xml", Model)
    return model.elements.variables.variable


def drop_duplicated_index(s: pd.Series | pd.DataFrame):
    return s.loc[~s.index.duplicated()]


def reduce_curve(s: pd.Series):
    "Returns a reduced equivalent (by interpolation) version of the series"
    s = drop_duplicated_index(s)
    s_prima = s.diff() / s.index.to_series().diff()
    mask = (s_prima.diff() == 0) & (s_prima.diff(-1) == 0)
    s = s.loc[~mask]
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


def infer_connection_vars(lib: str) -> tuple[str, str, str]:
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
    v_re = f"{prefix}_terminal_V_re"
    v_im = f"{prefix}_terminal_V_im"
    if lib.startswith("GeneratorSynchronous"):
        omega_ref = "generator_omegaRefPu_value"
        if lib == "GeneratorSynchronousFourWindingsTGov1Sexs":
            omega_ref = "governor_omegaRefPu"
        if lib == "GeneratorSynchronousThreeWindingsProportionalRegulationsTfoUva":
            v_re = "transformer_terminal1_V_re"
            v_im = "transformer_terminal1_V_im"
    else:
        omega_ref = f"{prefix}_omegaRefPu"
    return v_re, v_im, omega_ref


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
