import shutil
import subprocess
import tempfile
from pathlib import Path

import pandas as pd

from .config import settings
from .schemas import (
    CurveInput,
    CurvesInput,
    DynamicModelsArchitecture,
    Jobs,
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

    def __init__(self, jobs_file: str):
        self.jobs_file = Path(jobs_file).absolute()
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
        # Something better needs to be done here
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

    def run(self, executable=settings.DYNAWO_EXECUTABLE, verbose=False):
        "Execute Dynaωo simulation"
        subprocess.run(
            [executable, "jobs", self.jobs_file],
            capture_output=not verbose,
            check=True,
            text=True,
        )

    def read_curves(self):
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

    def duplicate(self, path: Path | str | None = None):
        "Create a new folder in the given path and copy all this simulation files there"
        new_case_folder = path or tempfile.mkdtemp(dir=settings.TMP_DIR)
        new_case_folder = Path(new_case_folder)
        shutil.copytree(self.base_folder, new_case_folder, dirs_exist_ok=True)
        return Simulation(new_case_folder / self.jobs_file.name)

    def update_crv(self, curves: list[CurveInput]):
        self.crv.curve = curves
        self.save()

    def delete(self):
        "Delete all files in the simulation base folder"
        return shutil.rmtree(self.base_folder)
