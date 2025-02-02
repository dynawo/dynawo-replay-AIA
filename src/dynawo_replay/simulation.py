import json
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from itertools import groupby
from pathlib import Path

import numpy as np
import pandas as pd

from .config import settings
from .exceptions import CaseNotPreparedForReplay, DynawoExecutionError
from .metrics import drop_duplicated_index
from .schemas.curves_input import CurveInput, CurvesInput
from .schemas.ddb_desc import Model
from .schemas.dyd import BlackBoxModel, Connect, DynamicModelsArchitecture
from .schemas.io import parser, serializer
from .schemas.jobs import InitValuesEntry, Jobs
from .schemas.parameters import Parameter, ParametersSet, Set


class Simulation:
    """Interface to interact with Dynaωo simulations"""

    TERMINAL_VARIABLES = [
        "generator_terminal_V_im",
        "generator_terminal_V_re",
        "generator_terminal_i_im",
        "generator_terminal_i_re",
        "generator_omegaRefPu_value",
    ]

    def __init__(self, jobs_file: str, dynawo: str = settings.DYNAWO_HOME):
        self.jobs_file = Path(jobs_file).absolute()
        self.dynawo_home = dynawo
        self.base_folder = self.jobs_file.parent
        self.name = self.base_folder.name
        jobs = parser.parse(jobs_file, Jobs)
        if len(jobs.job) != 1:
            raise NotImplementedError(
                "Only single-jobs simulations are currently supported"
            )
        self.job = jobs.job[0]
        self.dyd = parser.parse(self.dyd_file, DynamicModelsArchitecture)
        self.crv = parser.parse(self.crv_file, CurvesInput)
        self.par = parser.parse(self.par_file, ParametersSet)

    def save(self):
        with self.jobs_file.open("w") as f:
            serializer.write(f, Jobs(job=[self.job]))
        with self.crv_file.open("w") as f:
            serializer.write(f, self.crv)
        with self.dyd_file.open("w") as f:
            serializer.write(f, self.dyd)
        with self.par_file.open("w") as f:
            serializer.write(f, self.par)

    @property
    def par_file(self):
        # TODO: Something better needs to be done here
        return next(self.base_folder.glob("*.par"))

    @property
    def crv_file(self):
        if not self.job.outputs.curves:
            raise NotImplementedError(
                "Jobs with no output curves file not currently implemented."
            )
        return self.base_folder / self.job.outputs.curves.input_file

    @property
    def dyd_file(self):
        if len(self.job.modeler.dyn_models) != 1:
            raise NotImplementedError(
                "Simulations with more than one .dyd file are not currently supported"
            )
        return self.base_folder / self.job.modeler.dyn_models[0].dyd_file

    @property
    def output_curves_path(self):
        return self.base_folder / self.job.outputs.directory / "curves" / "curves.csv"

    @property
    def dump_init_folder(self):
        return (
            self.base_folder / self.job.outputs.directory / "initValues" / "globalInit"
        )

    @property
    def replayable_base_folder(self):
        return self.base_folder / "replay" / "terminals"

    @property
    def dynawo_version(self):
        return subprocess.run(
            [self.dynawo_home / "dynawo.sh", "version"],
            capture_output=True,
            check=True,
            text=True,
        ).stdout

    def run(self, verbose=False):
        "Execute Dynaωo simulation"
        try:
            subprocess.run(
                [self.dynawo_home / "dynawo.sh", "jobs", self.jobs_file],
                capture_output=not verbose,
                check=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            print(e.stdout)
            print(e.stderr)
            raise DynawoExecutionError() from e

    def list_all_possible_curves(self):
        curves = []
        for node in self.get_terminal_nodes():
            dyd_bbm = next(bbm for bbm in self.dyd.black_box_model if bbm.id == node)
            for var in self.list_available_vars(dyd_bbm.lib):
                curves.append(CurveInput(model=node, variable=var.name))
        return curves

    def list_available_vars(self, model):
        model = parser.parse(self.dynawo_home / "ddb" / f"{model}.desc.xml", Model)
        return model.elements.variables.variable

    def read_output_curves(self):
        "Read curves outputted from Dynaωo simulation as pandas dataframe"
        curves = pd.read_csv(self.output_curves_path, sep=";")
        curves.set_index("time", inplace=True)
        # Dynawo output CSV ends lines with trailing ; so we drop the last column
        curves.drop(columns=[curves.columns[-1]], inplace=True)
        return curves

    def get_terminal_nodes(self):
        return [
            model.id for model in self.dyd.black_box_model if "Generator" in model.lib
        ]

    def get_minimal_curves_for_replay(self):
        "Returns a list of the curves that need to be output in order to do a replay"
        return [
            CurveInput(model=model, variable=var)
            for model in self.get_terminal_nodes()
            for var in self.TERMINAL_VARIABLES
        ]

    def read_relevant_init_values(self):
        "If the simulation has been run with dumpInit, read the init values tied to references in par file"
        _init_values = {}
        for terminal in self.get_terminal_nodes():
            _init_values[terminal] = {}
            dump_init_file = self.dump_init_folder / f"dumpInitValues-{terminal}.txt"
            with dump_init_file.open("r") as f:
                _lines = f.readlines()
            dyd_bbm = next(
                bbm for bbm in self.dyd.black_box_model if bbm.id == terminal
            )
            pset = next(pset for pset in self.par.set if pset.id == dyd_bbm.par_id)
            for reference in pset.reference:
                line = next(line for line in _lines if line.startswith(reference.name))
                value = float(line.split("=")[1])
                _init_values[terminal][reference.name] = value
        return _init_values

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
        with self.replica(keep=keep_tmp) as rep:
            rep.crv.curve = minimal_curves
            rep.job.outputs.dump_init_values = InitValuesEntry(
                local=False, global_value=True
            )
            rep.save()
            rep.run()
            curves_df = rep.read_output_curves()
            init_values = rep.read_relevant_init_values()
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
                    json.dump(init_values[terminal], f)
        return curves_df, init_values

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
            with self.replica(keep=keep_tmp) as rep:
                rep.generate_ibus_table(terminal_df)
                terminal_bbm = next(
                    bbm for bbm in self.dyd.black_box_model if bbm.id == terminal
                )
                terminal_bbm.static_id = None
                rep.dyd = DynamicModelsArchitecture(
                    black_box_model=[
                        terminal_bbm,
                        BlackBoxModel(
                            id="IBus",
                            lib="InfiniteBusFromTable",
                            par_file=str(self.par_file.name),
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
                    pset for pset in self.par.set if pset.id == terminal_bbm.par_id
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
                    pset for pset in self.par.set if pset.id == self.job.solver.par_id
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
                                    value=str(rep.base_folder / "ibus_table.txt"),
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

    def generate_ibus_table(self, df, filename="ibus_table.txt"):
        "Create the .txt file used to pass a TableFile for the InfiniteBus model"
        U = np.hypot(
            df["generator_terminal_V_re"], df["generator_terminal_V_im"]
        ).rename("UPu")
        U_phase = np.arctan2(
            df["generator_terminal_V_im"], df["generator_terminal_V_re"]
        ).rename("UPhase")
        omega = df["generator_omegaRefPu_value"].rename("OmegaRefPu")
        with open(self.base_folder / filename, "w") as f:
            for i, s in enumerate((omega, U, U_phase)):
                f.write(f"#{i + 1}\n")
                f.write(f"\ndouble {s.name}({len(s)},2)\n")
                for time, value in s.items():
                    f.write(f"{time:.10f} {value:.10f}\n")

    def duplicate(self, path: Path | str | None = None):
        f"""
        Create a new folder copying all the files to work with an isolated simulation.
        If path is not provided, a new tmp folder will be created at {settings.TMP_DIR}.
        """
        new_case_folder = path or tempfile.mkdtemp(dir=settings.TMP_DIR)
        new_case_folder = Path(new_case_folder)
        shutil.copytree(
            self.base_folder,
            new_case_folder,
            ignore=shutil.ignore_patterns("reference", "outputs", "replay"),
            dirs_exist_ok=True,
        )
        return Simulation(
            new_case_folder / self.jobs_file.name, dynawo=self.dynawo_home
        )

    def delete(self):
        "Delete the base folder of the case"
        shutil.rmtree(self.base_folder)

    @contextmanager
    def replica(self, path: Path | str | None = None, keep: bool = False):
        """
        A context manager to work with an isolated replica of the case.
        The folder will be deleted on exit of the context manager if keep is False.
        """
        dup = self.duplicate(path)
        try:
            yield dup
        finally:
            if not keep:
                dup.delete()
