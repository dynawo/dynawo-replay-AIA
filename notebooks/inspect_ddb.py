import marimo

__generated_with = "0.11.7"
app = marimo.App(width="medium")


@app.cell
def _():
    from dynawo_replay import settings
    from dynawo_replay.schemas.ddb import Model, ExternalVariables
    from dynawo_replay.schemas.io import parser

    import pandas as pd 

    def get_var(model: Model, q: str, default_none: bool = True):
        candidates = [v.name for v in model.elements.variables.variable if q == v.name]
        if len(candidates) > 1:
            raise ValueError()
        elif len(candidates) == 0:
            if default_none:
                return None
            raise ValueError()
        else:
            return candidates[0]


    def get_prefix(model: Model):
        return model.elements.variables.variable[0].name.split("_")[0]

    _data = []
    for _file in settings.DYNAWO_HOME.glob("ddb/*.desc.xml"):
        if _file.name.startswith("dynawo_") or _file.name.startswith("DYN"):
            continue
        model = parser.parse(_file, Model)
        ext_var_file = _file.with_stem(model.name).with_suffix(".extvar")
        if ext_var_file.exists():
            external_vars = parser.parse(ext_var_file, ExternalVariables).variable
        else:
            external_vars = []
        prefix = model.elements.variables.variable[0].name.split("_")[0]
        v_re = get_var(model, f"{prefix}_terminal_V_re")
        v_im = get_var(model, f"{prefix}_terminal_V_im")
        omega_ref_pu = get_var(model, f"{prefix}_omegaRefPu")
        if not omega_ref_pu:
            omega_ref_pu = get_var(model, f"{prefix}_omegaRefPu_value")
        mandatory_vars = [v.id for v in external_vars if not v.optional and not v.default_value]
        _data.append(
            {
                "name": model.name,
                "prefix": prefix,
                "n_mandatory_ext_vars": len(mandatory_vars),
                "mandatory_ext_vars": sorted(mandatory_vars),
                "n_vars": len(model.elements.variables.variable),
                "n_ext_vars": len(external_vars),
                "terminal_V_re": v_re,
                "terminal_V_im": v_im,
                "omega_ref_pu": omega_ref_pu,
                "omega_is_external": omega_ref_pu in [v.id.replace(".", "_") for v in external_vars],
            }
        )

    df = pd.DataFrame(_data)
    df
    return (
        ExternalVariables,
        Model,
        df,
        ext_var_file,
        external_vars,
        get_prefix,
        get_var,
        mandatory_vars,
        model,
        omega_ref_pu,
        parser,
        pd,
        prefix,
        settings,
        v_im,
        v_re,
    )


@app.cell
def _(df):
    df["supported"] = (
        ~df["name"].str.contains("SignalN")
        & ~df["name"].str.contains("NoPlantControl")
        & ~df["name"].str.contains("Rpcl")
        & ~df["name"].str.contains("ThreePhase")  # Mandatory variables pin[i]
        & ~df["name"].str.contains("GoverAnsal")  # Mandatory voltageRegulator_omegaRefPu
        & ~df["name"].str.contains("GoverSt2VR")  # Two generators or governor_PmGtPu
        & (
            df["name"].str.startswith("GeneratorSynchronous")  # Synchronous generators
            | df["name"].str.startswith("Photovoltaic")  # Photovoltaic panels
            | df["name"].str.startswith("WTG")  # Wind Turbines
            | df["name"].str.startswith("IECWPP")  # Wind Turbines
            | df["name"].str.startswith("BESS")  # Batteries
        )
    )
    df["is_generator"] = df["prefix"].isin([
        'generator', 'photovoltaics',
        'WPP', 'WT', 'WT4A', 'WT4B', 'WTG4A', 'WTG4B', 
        'BESScb', 
    ])
    df.sort_values("name", inplace=True)
    df.loc[df["supported"]]
    return


@app.cell
def _(df):
    df.loc[df["supported"]]["mandatory_ext_vars"].astype(str).sort_values().unique()
    return


@app.cell
def _(df, pd):
    def infer_connection_vars(lib: str) -> tuple[str, str, str, str]:
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
        if lib in (
            "GeneratorSynchronousThreeWindingsProportionalRegulationsTfoUva",
            "GeneratorSynchronousThreeWindingsGoverPropVRPropIntTfoUva",
        ):
            v_re = "transformer_terminal1_V_re"
            v_im = "transformer_terminal1_V_im"
        elif lib in (
            "GeneratorSynchronousThreeWindingsProportionalRegulationsTfoAuxUva",
            "GeneratorSynchronousThreeWindingsProportionalRegulationsAuxUva"
        ):
            v_re = "coupling_terminal1_V_re"
            v_im = "coupling_terminal1_V_im"
        else:
            v_re = f"{prefix}_terminal_V_re"
            v_im = f"{prefix}_terminal_V_im"
        if lib.startswith("GeneratorSynchronous"):
            omega_ref = "generator_omegaRefPu_value"
            if lib == "GeneratorSynchronousFourWindingsTGov1Sexs":
                omega_ref = "governor_omegaRefPu"
        else:
            omega_ref = f"{prefix}_omegaRefPu"
        if lib in (
            "GeneratorSynchronousThreeWindingsGoverPropVRPropIntUva",
            "GeneratorSynchronousThreeWindingsProportionalRegulationsAuxUva",
            "GeneratorSynchronousThreeWindingsProportionalRegulationsUva",
        ):
            uva_u_monitored = "underVoltageAutomaton_UMonitoredPu"
        else:
            uva_u_monitored = None
        return omega_ref, v_re, v_im, uva_u_monitored

    supported_df = df.loc[df["supported"]][["name"]]
    supported_df[["omega", "v_re", "v_im", "uva"]] = supported_df['name'].apply(lambda x: pd.Series(infer_connection_vars(x)))
    supported_df.set_index("name", inplace=True)
    supported_df

    return infer_connection_vars, supported_df


@app.cell(disabled=True)
def _(supported_df):
    supported_df.to_csv("supported_models.csv")
    return


@app.cell
def _():
    from dynawo_replay.utils import load_supported_models


    models = load_supported_models()
    models["BESScbWeccCurrentSource"]
    return load_supported_models, models


if __name__ == "__main__":
    app.run()
