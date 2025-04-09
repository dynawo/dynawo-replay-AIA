import json
import shutil
from functools import cached_property

import numpy as np
import pandas as pd

from dynawo_replay.schemas.dyd import BlackBoxModel, Connect

from .config import PACKAGE_DIR
from .exceptions import CaseNotPreparedForReplay, UnresolvedReference
from .schemas.curves_input import CurveInput
from .schemas.jobs import InitValuesEntry
from .simulation import Case
from .utils import (
    list_available_vars,
    load_supported_models,
    postprocess_curve,
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
        supported_models = load_supported_models()
        return {
            bbm.id: ReplayableElement(
                case=self, id=bbm.id, connection_variables=supported_models.get(bbm.lib)
            )
            for bbm in self.dyd.black_box_model
            if bbm.lib in supported_models
        }

    def generate_replayable_base(
        self,
        elements: list[str] = [],
        keep_tmp: bool = False,
        keep_original_solver: bool = False,
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
        prep_folder = self.base_folder / "replay" / "_prep"
        with self.replica(path=prep_folder, keep=keep_tmp) as rep:
            rep.crv.curve = [crv for el in _elements for crv in el.get_base_curves()]
            rep.job.outputs.dump_init_values = InitValuesEntry(
                local=False,
                global_value=True,
                init=True,
            )
            rep.job.outputs.curves.export_mode = "CSV"
            rep.save()
            rep.run()
            curves_df = rep.read_output_curves()
            init_params = rep.read_init_params()
        self.replay_core_folder.mkdir(parents=True, exist_ok=True)
        for el in _elements:
            _df = curves_df[[f"{el.id}_{c.variable}" for c in el.get_base_curves()]]
            _df.columns = _df.columns.str.removeprefix(el.id + "_")
            _df.to_parquet(
                self.replay_core_folder / f"{el.sanitized_id}.parquet",
                engine="pyarrow",
                compression="snappy",
            )
            _init_params = el.filter_relevant_init_params(init_params[el.id])
            with (self.replay_core_folder / f"{el.sanitized_id}_initValues.json").open(
                "w"
            ) as f:
                json.dump(_init_params, f)
        self.create_replay_template(keep_original_solver=keep_original_solver)

    def create_replay_template(self, keep_original_solver=False):
        base_template = Case(PACKAGE_DIR / "templates" / "replay_base" / "replay.jobs")
        template = base_template.duplicate(self.replay_template_folder)
        template.job.simulation.start_time = self.job.simulation.start_time
        template.job.simulation.stop_time = self.job.simulation.stop_time
        if keep_original_solver:
            template.job.solver.lib = self.job.solver.lib
            template.par_dict["Solver"][:] = self.par_dict[self.job.solver.par_id]
        template.save()

    def replay(self, element_id: str, curves: list[str], keep_tmp=True):
        """
        Replay a local simulation for the given element retrieving the demanded curves.
        The case must be previously prepared with .generate_replayable_base() method.
        This simulation is executed in a replicated folder for the parent case where the
        dynamic architecture is rewritten to replace the rest of the network as an InfiniteBus.
        No .iidm file is generated for this case, and the references in model parameters are read
        from init values dumped in the case preparation.
        The local simulation case folder is deleted if keep_tmp is False.
        """
        element = self.replayable_elements[element_id]
        return element.replay(curves, keep_tmp=keep_tmp)

    def calculate_reference_curves(
        self, element_id: str, curves: list[str], keep_tmp=False
    ):
        """
        Run the large case scenario extracting the given list of curves.
        This method is intended to be used only for later comparing the replay
        functionality in benchmarks or tests.
        """
        with self.replica(keep=keep_tmp) as rep:
            rep.crv.curve = [CurveInput(model=element_id, variable=v) for v in curves]
            rep.job.outputs.curves.export_mode = "CSV"
            rep.save()
            rep.run()
            return rep.read_output_curves()


class ReplayableElement:
    def __init__(self, case: Case, id: str, connection_variables: dict):
        self.case = case
        self.id = id
        self.bbm = self.case.bbm_dict[id]
        self.params = self.case.par_dict[self.bbm.par_id]
        self.lib = self.bbm.lib
        self.connection_variables = connection_variables
        self.omega_ref, self.v_re, self.v_im, self.uva = (
            self.connection_variables.values()
        )

    @cached_property
    def replayable_variables(self):
        return list_available_vars(self.lib, dynawo=self.case.dynawo_home)

    @cached_property
    def sanitized_id(self):
        "Returns an id that can be embedded in a path by replacing '/' by '_'."
        return self.id.replace("/", "_").replace(" ", "_").replace(".", "_")

    def get_base_curves(self) -> list[CurveInput]:
        return [
            CurveInput(model=self.id, variable=var)
            for var in self.connection_variables.values()
            if var
        ]

    def filter_relevant_init_params(self, init_params) -> dict:
        "Retrieve only params that are actually tied to a reference"
        try:
            return {ref.name: init_params[ref.name] for ref in self.params.reference}
        except KeyError as e:
            raise UnresolvedReference(self.id, *e.args)

    def replay(self, curves: list[str], keep_tmp=True):
        "Perform the replay for this element retrieving the given curves"
        df, init_values = self.read_replayable_base()
        replay_template = self.case.replay_template_case
        replay_folder = self.case.base_folder / "replay" / self.sanitized_id
        with replay_template.replica(path=replay_folder, keep=keep_tmp) as case:
            ibus_table_path = case.base_folder / "ibus_table.txt"
            self.write_ibus_table(df, ibus_table_path)
            case.dyd.black_box_model[0].id = self.id
            case.dyd.black_box_model[0].lib = self.lib
            case.dyd.connect[0].id1 = self.id
            case.dyd.connect[0].var1 = self.v_re[:-5]
            case.dyd.connect[1].id1 = self.id
            case.dyd.connect[1].var1 = self.omega_ref
            case.par.set[0].par[:] = solve_references(self.params, init_values).par
            case.par.set[2].par[-1].value = str(ibus_table_path)
            if self.uva:
                uva_ibus_table_path = case.base_folder / "uva_ibus_table.txt"
                self.write_uva_ibus_table(df, uva_ibus_table_path)
                case.dyd.black_box_model.append(
                    BlackBoxModel(
                        id="UvaIBus",
                        lib="InfiniteBusFromTable",
                        par_file="replay.par",
                        par_id="IBus",
                    )
                )
                case.dyd.connect.append(
                    Connect(
                        id1=self.id,
                        var1=self.uva,
                        id2="IBus",
                        var2="infiniteBus_terminal",
                    )
                )
                case.par.set[3].par[-1].value = str(uva_ibus_table_path)
            case.crv.curve = [CurveInput(model=self.id, variable=v) for v in curves]
            case.save()
            case.run()
            replayed_df = case.read_output_curves()
            replayed_df = replayed_df.apply(postprocess_curve)
            return replayed_df

    def read_replayable_base(self):
        "Read connection curves dataframe and the init values"
        try:
            df = pd.read_parquet(
                self.case.replay_core_folder / f"{self.sanitized_id}.parquet"
            )
            dump_init_file = (
                self.case.replay_core_folder / f"{self.sanitized_id}_initValues.json"
            )
            with dump_init_file.open("r") as f:
                init_values = json.load(f)
            return df, init_values
        except FileNotFoundError:
            raise CaseNotPreparedForReplay()

    def write_series_in_table(self, series, i, f):
        f.write(f"#{i + 1}\n")
        f.write(f"\ndouble {series.name}({len(series)},2)\n")
        for time, value in series.items():
            f.write(f"{time:.10f} {value:.10f}\n")

    def write_ibus_table(self, df, filename="ibus_table.txt"):
        "Create the .txt file used to pass a TableFile for the InfiniteBus model"
        U = reduce_curve(np.hypot(df[self.v_re], df[self.v_im]).rename("UPu"))
        U_phase = reduce_curve(
            np.arctan2(df[self.v_im], df[self.v_re]).rename("UPhase")
        )
        omega = reduce_curve(df[self.omega_ref].rename("OmegaRefPu"))
        with open(filename, "w") as f:
            for i, s in enumerate((omega, U, U_phase)):
                self.write_series_in_table(s, i, f)

    def write_uva_ibus_table(self, df, filename="uva_ibus_table.txt"):
        U = reduce_curve(df[self.uva]).rename("UPu")
        with open(filename, "w") as f:
            self.write_series_in_table(U, 1, f)
