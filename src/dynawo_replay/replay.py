import json
from functools import cached_property
from itertools import groupby

import numpy as np
import pandas as pd

from .config import PACKAGE_DIR
from .exceptions import CaseNotPreparedForReplay, UnresolvedReference
from .schemas.curves_input import CurveInput
from .schemas.jobs import InitValuesEntry
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
    def replay_core_folder(self):
        return self.base_folder / "replay" / "_core"

    @cached_property
    def replay_template_folder(self):
        return self.base_folder / "replay" / "_template"

    @cached_property
    def replay_template_case(self):
        return Case(
            self.replay_template_folder / "replay.jobs",
            dynawo=self.dynawo_home,
        )

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
    ):
        """
        Run the complete network simulation and generate the data necessary for later replay.
        The simulation is executed in a replica folder where we set the curves to output to be
        the minimal curves for each terminal node in the network.
        We also make sure to dump init values and store the relevant references.
        The replica is deleted after the simulation is done if keep_tmp=False.
        The results are saved in self.replay_core_folder, one file for each terminal node.
        This will also create the base template for local replay.
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
        self.replay_core_folder.mkdir(parents=True, exist_ok=True)
        for el in _elements:
            _df = curves_df[[f"{el.id}_{c.variable}" for c in el.get_base_curves()]]
            _df.columns = _df.columns.str.removeprefix(el.id + "_")
            _df.to_parquet(
                self.replay_core_folder / f"{el.id}.parquet",
                engine="pyarrow",
                compression="snappy",
            )
            _init_params = el.filter_relevant_init_params(init_params[el.id])
            with (self.replay_core_folder / f"{el.id}_initValues.json").open("w") as f:
                json.dump(_init_params, f)
        self.create_replay_template()

    def create_replay_template(self, keep_original_solver=False):
        base_template = Case(PACKAGE_DIR / "templates" / "replay_base" / "replay.jobs")
        template = base_template.duplicate(self.replay_template_folder)
        template.job.simulation = self.job.simulation
        if keep_original_solver:
            template.job.solver.lib = self.job.solver.lib
            template.par_dict["Solver"][:] = self.par_dict[self.job.solver.par_id]
        template.save()

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
        replay_template = self.case.replay_template_case
        replay_folder = self.case.base_folder / "replay" / self.id
        with replay_template.replica(path=replay_folder, keep=keep_tmp) as case:
            ibus_table_path = case.base_folder / "ibus_table.txt"
            self.write_ibus_table(df, ibus_table_path)
            case.dyd.black_box_model[0].id = self.id
            case.dyd.black_box_model[0].lib = self.lib
            case.dyd.connect[0].id1 = self.id
            case.dyd.connect[0].var1 = self.v_re[:-5]
            case.dyd.connect[1].id1 = self.id
            case.dyd.connect[1].var1 = self.omega_ref
            case.par.set[0].par[:] = solve_references(
                self.params, init_values
            ).par  # Set element params
            case.par.set[2].par[-1].value = str(
                ibus_table_path
            )  # Set final iBus table path
            case.crv.curve = curves
            case.save()
            case.run()
            return case.read_output_curves()

    def read_replayable_base(self):
        "Read connection curves dataframe and the init values"
        try:
            df = pd.read_parquet(self.case.replay_core_folder / f"{self.id}.parquet")
            dump_init_file = self.case.replay_core_folder / f"{self.id}_initValues.json"
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
