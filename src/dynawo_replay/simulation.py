import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from itertools import groupby
from pathlib import Path

import pandas as pd

from .config import settings
from .exceptions import CaseNotPreparedForReplay
from .schemas import (
    CurveInput,
    CurvesInput,
    DynamicModelsArchitecture,
    Jobs,
    Model,
    ParametersSet,
    parser,
    serializer,
)


class Simulation:
    """Interface to interact with Dynaωo simulations"""

    GENERATOR_TERMINAL_VARIABLES = [
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
        return next(self.base_folder.glob("*.par"), None)

    @property
    def crv_file(self):
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
    def dynawo_executable(self):
        return self.dynawo_home / "dynawo.sh"

    @property
    def dynawo_version(self):
        return subprocess.run(
            [self.dynawo_executable, "version"],
            capture_output=True,
            check=True,
            text=True,
        ).stdout

    def run(self, verbose=False):
        "Execute Dynaωo simulation"
        subprocess.run(
            [self.dynawo_executable, "jobs", self.jobs_file],
            capture_output=not verbose,
            check=True,
            text=True,
        )

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

    def get_minimal_curves_for_replay(self):
        "Returns a list of the curves that need to be output in order to do a replay"
        for model in self.dyd.black_box_model:
            if "Generator" in model.lib:
                for var in self.GENERATOR_TERMINAL_VARIABLES:
                    yield CurveInput(model=model.id, variable=var)

    @property
    def replayable_base_folder(self):
        return self.base_folder / "replay" / "global"

    def generate_replayable_base(self, keep_tmp=False, save=True):
        minimal_curves = list(self.get_minimal_curves_for_replay())
        with self.duplicate(keep=keep_tmp) as dup:
            dup.update_crv(minimal_curves)
            dup.save()
            dup.run()
            curves_df = dup.read_output_curves()
        if save:
            output_folder = self.replayable_base_folder
            output_folder.mkdir(parents=True, exist_ok=True)
            curves_df.to_parquet(
                output_folder / "curves.parquet", engine="pyarrow", compression="snappy"
            )
        return curves_df

    def replay(self, curves: list[CurveInput], keep_tmp=False):
        global_curves_file = self.replayable_base_folder / "curves.parquet"
        try:
            global_curves_df = pd.read_parquet(global_curves_file)
        except FileNotFoundError:
            raise CaseNotPreparedForReplay()
        curves_dfs = []
        for generator, curves_ in groupby(curves, key=lambda x: x.model):
            with self.duplicate(keep=keep_tmp) as dup:
                print("generator", generator)
                print("global.shape", global_curves_df.shape)
                dup.update_crv(list(curves_))
                dup.save()
                dup.run()
                curves_df = dup.read_output_curves()
                curves_dfs.append(curves_df)
        return pd.concat(curves_dfs)

    def update_crv(self, curves: list[CurveInput]):
        self.crv.curve = curves
        self.save()

    @contextmanager
    def duplicate(self, path: Path | str | None = None, keep: bool = False):
        f"""
        Create a new folder copying all the files to work with an isolated simulation.
        If path is not provided, a new tmp folder will be created at {settings.TMP_DIR}.
        The folder will be deleted on exit of the context manager if keep is False.
        """
        new_case_folder = path or tempfile.mkdtemp(dir=settings.TMP_DIR)
        new_case_folder = Path(new_case_folder)
        shutil.copytree(self.base_folder, new_case_folder, dirs_exist_ok=True)
        try:
            yield Simulation(
                new_case_folder / self.jobs_file.name, dynawo=self.dynawo_home
            )
        finally:
            if not keep:
                shutil.rmtree(new_case_folder)
