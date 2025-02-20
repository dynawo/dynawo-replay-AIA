import json
from dataclasses import replace
from functools import cached_property
from itertools import groupby

import numpy as np
import pandas as pd

from .exceptions import CaseNotPreparedForReplay, UnresolvedReference
from .schemas.curves_input import CurveInput
from .schemas.dyd import BlackBoxModel, Connect, DynamicModelsArchitecture
from .schemas.jobs import InitValuesEntry
from .schemas.parameters import Parameter, ParametersSet, Set
from .simulation import Case
from .utils import (
    combine_dataframes,
    infer_connection_vars,
    list_available_vars,
    reduce_curve,
    solve_references,
)


class ReplayableCase(Case):
    @cached_property
    def replayable_base_folder(self):
        return self.base_folder / "replay" / "terminals"

    @cached_property
    def replayable_elements(self):
        return {
            bbm.id: ReplayableElement(case=self, id=bbm.id)
            for bbm in self.dyd.black_box_model
            if (
                "SignalN" not in bbm.lib
                and "NoPlantControl" not in bbm.lib
                and (
                    bbm.lib.startswith("GeneratorSynchronous")
                    or bbm.lib.startswith("Photovoltaic")
                    or bbm.lib.startswith("WTG")
                    or bbm.lib.startswith("IECWPP")
                    or bbm.lib.startswith("BESScb")
                )
            )
        }

    def generate_replayable_base(
        self,
        elements: list[str] = [],
        keep_tmp: bool = False,
        save: bool = False,
    ):
        """
        Run the complete network simulation and generate the data necessary for later replay.
        The simulation is executed in a replica folder where we set the curves to output to be
        the minimal curves for each terminal node in the network.
        We also make sure to dump init values and store the relevant references.
        The replica is deleted after the simulation is done if keep_tmp=False.
        The results are saved in self.replayable_base_folder, one file for each terminal node.
        """
        if not elements:
            _elements = self.replayable_elements.values()
        else:
            _elements = [self.replayable_elements[el] for el in elements]
        with self.replica(keep=keep_tmp) as rep:
            rep.crv.curve = [crv for el in _elements for crv in el.get_base_curves()]
            rep.job.outputs.dump_init_values = InitValuesEntry(
                local=False, global_value=True
            )
            rep.save()
            rep.run()
            curves_df = rep.read_output_curves()
            init_params = rep.read_init_params()
        if save:
            output_folder = self.replayable_base_folder
            output_folder.mkdir(parents=True, exist_ok=True)
            for el in _elements:
                _df = curves_df[[f"{el.id}_{c.variable}" for c in el.get_base_curves()]]
                _df.columns = _df.columns.str.removeprefix(el.id + "_")
                _df.to_parquet(
                    output_folder / f"{el.id}.parquet",
                    engine="pyarrow",
                    compression="snappy",
                )
                _init_params = el.filter_relevant_init_params(init_params[el.id])
                with (output_folder / f"{el.id}_initValues.json").open("w") as f:
                    json.dump(_init_params, f)
        return curves_df, init_params

    def replay(self, curves: list[CurveInput], keep_tmp=False):
        """
        Replay a local simulation for each one of the elements associated to the given curves.
        The case must be previously prepared with .generate_replayable_base() method.
        These local simulations are run in a replicated folders where the dynamic architecture is
        rewritten to only contain the terminal node and a InfiteBusFromTable model.
        No .iidm file is generated for this case, and the references in model parameters are read
        from init values dumped in the case preparation.
        All curves generated are combined into a single dataframe where the values are interpolated
        to a full time index.
        The replicated folders are deleted if keep_tmp is False.
        """
        curves_dfs = []
        for element_id, curves_ in groupby(curves, key=lambda x: x.model):
            element = self.replayable_elements[element_id]
            curves_dfs.append(element.replay(list(curves_), keep_tmp=keep_tmp))
        return combine_dataframes(curves_dfs)

    def calculate_reference_curves(self, curves: list[CurveInput], keep_tmp=False):
        """
        Run the large case scenario extracting the given list of curves.
        This method is intended to be used only for later comparing the replay
        functionality in benchmarks or tests.
        """
        with self.replica(keep=keep_tmp) as rep:
            rep.crv.curve = curves
            rep.save()
            rep.run()
            return rep.read_output_curves()


class ReplayableElement:
    def __init__(self, case: Case, id: str):
        self.case = case
        self.id = id
        self.bbm = self.case.bbm_dict[id]
        self.params = self.case.par_dict[self.bbm.par_id]
        self.lib = self.bbm.lib
        self.connection_variables = infer_connection_vars(self.lib)
        self.v_re, self.v_im, self.omega_ref = self.connection_variables

    @cached_property
    def replayable_variables(self):
        return list_available_vars(self.lib, dynawo=self.case.dynawo_home)

    def get_base_curves(self) -> list[CurveInput]:
        return [
            CurveInput(model=self.id, variable=var) for var in self.connection_variables
        ]

    def filter_relevant_init_params(self, init_params) -> dict:
        "Retrieve only params that are actually tied to a reference"
        try:
            return {ref.name: init_params[ref.name] for ref in self.params.reference}
        except KeyError:
            raise UnresolvedReference()

    def replay(self, curves: list[CurveInput], keep_tmp=False):
        "Perform the replay for this element retrieving the given curves"
        df, init_values = self.read_replayable_base()
        with self.case.replica(keep=keep_tmp) as _case:
            ibus_table_path = _case.base_folder / "ibus_table.txt"
            self.write_ibus_table(df, ibus_table_path)
            _case.dyd = DynamicModelsArchitecture(
                black_box_model=[
                    replace(_case.bbm_dict[self.id], static_id=None),
                    BlackBoxModel(
                        id="IBus",
                        lib="InfiniteBusFromTable",
                        par_file=str(_case.par_file.name),
                        par_id="IBus",
                    ),
                ],
                connect=[
                    Connect(
                        id1=self.id,
                        var1=self.v_re[:-5],
                        id2="IBus",
                        var2="infiniteBus_terminal",
                    ),
                    Connect(
                        id1=self.id,
                        var1=self.omega_ref,
                        id2="IBus",
                        var2="infiniteBus_omegaRefPu",
                    ),
                ],
            )
            _case.par = ParametersSet(
                set=[
                    solve_references(_case.par_dict[self.bbm.par_id], init_values),
                    _case.par_dict[_case.job.solver.par_id],
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
            _case.job.simulation.precision = 1e-8
            _case.job.modeler.network = None
            _case.crv.curve = curves
            _case.save()
            _case.run()
            return _case.read_output_curves()

    def read_replayable_base(self):
        "Read connection curves dataframe and the init values"
        try:
            df = pd.read_parquet(
                self.case.replayable_base_folder / f"{self.id}.parquet"
            )
            dump_init_file = (
                self.case.replayable_base_folder / f"{self.id}_initValues.json"
            )
            with dump_init_file.open("r") as f:
                init_values = json.load(f)
            return df, init_values
        except FileNotFoundError:
            raise CaseNotPreparedForReplay()

    def write_ibus_table(self, df, filename="ibus_table.txt"):
        "Create the .txt file used to pass a TableFile for the InfiniteBus model"
        U = reduce_curve(np.hypot(df[self.v_re], df[self.v_im]).rename("UPu"))
        U_phase = reduce_curve(
            np.arctan2(df[self.v_im], df[self.v_re]).rename("UPhase")
        )
        omega = reduce_curve(df[self.omega_ref].rename("OmegaRefPu"))
        with open(filename, "w") as f:
            for i, s in enumerate((omega, U, U_phase)):
                f.write(f"#{i + 1}\n")
                f.write(f"\ndouble {s.name}({len(s)},2)\n")
                for time, value in s.items():
                    f.write(f"{time:.10f} {value:.10f}\n")
