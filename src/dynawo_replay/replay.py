import json
from itertools import groupby

import numpy as np
import pandas as pd

from .exceptions import CaseNotPreparedForReplay
from .metrics import drop_duplicated_index
from .schemas.curves_input import CurveInput
from .schemas.ddb_desc import Model
from .schemas.dyd import BlackBoxModel, Connect, DynamicModelsArchitecture
from .schemas.io import parser
from .schemas.jobs import InitValuesEntry
from .schemas.parameters import Parameter, ParametersSet, Set
from .simulation import Case


class Replay:
    TERMINAL_VARIABLES = [
        "generator_terminal_V_im",
        "generator_terminal_V_re",
        "generator_terminal_i_im",
        "generator_terminal_i_re",
        "generator_omegaRefPu_value",
    ]

    def __init__(self, case: Case):
        self.case = case

    @property
    def replayable_base_folder(self):
        return self.case.base_folder / "replay" / "terminals"

    def list_all_possible_curves(self):
        curves = []
        for node in self.get_terminal_nodes():
            dyd_bbm = next(bbm for bbm in self.dyd.black_box_model if bbm.id == node)
            for var in self.list_available_vars(dyd_bbm.lib):
                curves.append(CurveInput(model=node, variable=var.name))
        return curves

    def list_available_vars(self, model):
        model = parser.parse(self.case.dynawo_home / "ddb" / f"{model}.desc.xml", Model)
        return model.elements.variables.variable

    def get_terminal_nodes(self):
        return [
            model.id
            for model in self.case.dyd.black_box_model
            if "Generator" in model.lib
        ]

    def get_minimal_curves_for_replay(self):
        "Returns a list of the curves that need to be output in order to do a replay"
        return [
            CurveInput(model=model, variable=var)
            for model in self.get_terminal_nodes()
            for var in self.TERMINAL_VARIABLES
        ]

    def filter_relevant_init_params(self, init_params):
        "Retrieve only init params that are actually tied to a terminal node reference"
        relevant_params = {}
        for terminal in self.get_terminal_nodes():
            dyd_bbm = next(
                bbm for bbm in self.case.dyd.black_box_model if bbm.id == terminal
            )
            pset = next(pset for pset in self.case.par.set if pset.id == dyd_bbm.par_id)
            relevant_params[terminal] = {
                ref.name: init_params[terminal][ref.name] for ref in pset.reference
            }
        return relevant_params

    def generate_replayable_base(self, keep_tmp=False, save=False):
        """
        Run the large scale scenario and generate the data necessary for later replay.
        The simulation is executed in a replica folder where we set the curves to output to be
        the minimal curves for each terminal node in the network.
        We also make sure to dump init values and store the relevant references.
        The replica is deleted after the simulation is done if keep_tmp=False.
        The results are saved in self.replayable_base_folder, one file for each terminal node.
        """
        minimal_curves = self.get_minimal_curves_for_replay()
        with self.case.replica(keep=keep_tmp) as rep:
            rep.crv.curve = minimal_curves
            rep.job.outputs.dump_init_values = InitValuesEntry(
                local=False, global_value=True
            )
            rep.save()
            rep.run()
            curves_df = rep.read_output_curves()
            init_params = rep.read_init_params()
            init_params = self.filter_relevant_init_params(init_params)
        if save:
            output_folder = self.replayable_base_folder
            output_folder.mkdir(parents=True, exist_ok=True)
            for terminal, curves in groupby(minimal_curves, key=lambda x: x.model):
                _df = curves_df[[f"{terminal}_{curve.variable}" for curve in curves]]
                _df.columns = _df.columns.str.removeprefix(terminal + "_")
                _df.to_parquet(
                    output_folder / f"{terminal}.parquet",
                    engine="pyarrow",
                    compression="snappy",
                )
                with (output_folder / f"{terminal}_initValues.json").open("w") as f:
                    json.dump(init_params[terminal], f)
        return curves_df, init_params

    def replay(self, curves: list[CurveInput], keep_tmp=False):
        """
        Replay a local simulation for each one of the terminal nodes associated to the given curves.
        The case must be previously prepared with .generate_replayable_case() method.
        These local simulations are run in a replicated folders where the dynamic architecture is
        rewritten to only contain the terminal node and a InfiteBusFromTable model.
        No .iidm file is generated for this case, and the references in model parameters are read
        from init values dumped in the case preparation.
        All curves generated are combined into a single dataframe where the values are interpolated
        to a full time index (it contains time index for each simulation).
        The replicated folders are deleted if keep_tmp is False.
        """
        curves_dfs = []
        for terminal, curves_ in groupby(curves, key=lambda x: x.model):
            try:
                terminal_df = pd.read_parquet(
                    self.replayable_base_folder / f"{terminal}.parquet"
                )
                dump_init_file = (
                    self.replayable_base_folder / f"{terminal}_initValues.json"
                )
                with dump_init_file.open("r") as f:
                    terminal_init_values = json.load(f)
            except FileNotFoundError:
                raise CaseNotPreparedForReplay()
            with self.case.replica(keep=keep_tmp) as rep:
                ibus_table_path = rep.base_folder / "ibus_table.txt"
                self.generate_ibus_table(terminal_df, ibus_table_path)
                terminal_bbm = next(
                    bbm for bbm in rep.dyd.black_box_model if bbm.id == terminal
                )
                terminal_bbm.static_id = None
                rep.dyd = DynamicModelsArchitecture(
                    black_box_model=[
                        terminal_bbm,
                        BlackBoxModel(
                            id="IBus",
                            lib="InfiniteBusFromTable",
                            par_file=str(rep.par_file.name),
                            par_id="IBus",
                        ),
                    ],
                    connect=[
                        Connect(
                            id1=terminal,
                            var1="generator_terminal",
                            id2="IBus",
                            var2="infiniteBus_terminal",
                        ),
                        Connect(
                            id1=terminal,
                            var1="generator_omegaRefPu_value",
                            id2="IBus",
                            var2="infiniteBus_omegaRefPu",
                        ),
                    ],
                )
                terminal_params = next(
                    pset for pset in rep.par.set if pset.id == terminal_bbm.par_id
                )
                for reference in terminal_params.reference:
                    terminal_params.par.append(
                        Parameter(
                            name=reference.name,
                            type_value=reference.type_value,
                            value=terminal_init_values[reference.name],
                        )
                    )
                terminal_params.reference = []
                solver_params = next(
                    pset for pset in rep.par.set if pset.id == rep.job.solver.par_id
                )
                rep.par = ParametersSet(
                    set=[
                        terminal_params,
                        solver_params,
                        Set(
                            id="IBus",
                            par=[
                                Parameter(
                                    name="infiniteBus_UPuTableName",
                                    type_value="STRING",
                                    value="UPu",
                                ),
                                Parameter(
                                    name="infiniteBus_UPhaseTableName",
                                    type_value="STRING",
                                    value="UPhase",
                                ),
                                Parameter(
                                    name="infiniteBus_OmegaRefPuTableName",
                                    type_value="STRING",
                                    value="OmegaRefPu",
                                ),
                                Parameter(
                                    name="infiniteBus_TableFile",
                                    type_value="STRING",
                                    value=str(ibus_table_path),
                                ),
                            ],
                        ),
                    ]
                )
                rep.job.simulation.precision = 1e-8
                rep.job.modeler.network = None
                rep.crv.curve = list(curves_)
                rep.save()
                rep.run()
                curves_df = rep.read_output_curves()
                curves_dfs.append(curves_df)
        combined_df = drop_duplicated_index(curves_dfs[0])
        for df in curves_dfs[1:]:
            combined_df = pd.merge(
                combined_df,
                drop_duplicated_index(df),
                left_index=True,
                right_index=True,
                how="outer",
            )
        combined_df = combined_df.sort_index().interpolate()
        return combined_df

    def calculate_reference_curves(self, curves: list[CurveInput], keep_tmp=False):
        """
        Run the large case scenario extracting the given list of curves.
        This method is intended to be used only for later comparing the replay
        functionality in benchmarks or tests.
        """
        with self.case.replica(keep=keep_tmp) as rep:
            rep.crv.curve = curves
            rep.save()
            rep.run()
            return rep.read_output_curves()

    def generate_ibus_table(self, df, filename="ibus_table.txt"):
        "Create the .txt file used to pass a TableFile for the InfiniteBus model"
        U = np.hypot(
            df["generator_terminal_V_re"], df["generator_terminal_V_im"]
        ).rename("UPu")
        U_phase = np.arctan2(
            df["generator_terminal_V_im"], df["generator_terminal_V_re"]
        ).rename("UPhase")
        omega = df["generator_omegaRefPu_value"].rename("OmegaRefPu")
        with open(filename, "w") as f:
            for i, s in enumerate((omega, U, U_phase)):
                f.write(f"#{i + 1}\n")
                f.write(f"\ndouble {s.name}({len(s)},2)\n")
                for time, value in s.items():
                    f.write(f"{time:.10f} {value:.10f}\n")
