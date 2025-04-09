import shutil
import subprocess
import tempfile
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from .config import settings
from .exceptions import DynawoExecutionError
from .schemas.curves_input import CurvesInput
from .schemas.dyd import DynamicModelsArchitecture
from .schemas.io import parser, serializer
from .schemas.jobs import CurvesEntry, Jobs
from .schemas.parameters import ParametersSet


class Case:
    """Interface to interact with Dynaωo simulations"""

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
        self.name = self.job.name
        self.dyd = parser.parse(self.dyd_file, DynamicModelsArchitecture)
        self.crv = parser.parse(self.crv_file, CurvesInput)
        self.par = parser.parse(self.par_file, ParametersSet)
        self.par_dict = {pset.id: pset for pset in self.par.set}
        self.bbm_dict = {bbm.id: bbm for bbm in self.dyd.black_box_model}

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
        filename = next(self.base_folder.glob("*.par"), None)
        if not filename:
            filename = next(self.base_folder.glob("*PAR*"))
        return filename

    @property
    def crv_file(self):
        if not self.job.outputs.curves:
            self.job.outputs.curves = CurvesEntry(
                input_file=self.jobs_file.with_suffix(".crv"), export_mode="CSV"
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
        return self.base_folder / self.job.outputs.directory / "initValues"

    def run(self, verbose=False, timeout=600):
        "Execute Dynaωo simulation"
        try:
            subprocess.run(
                [self.dynawo_home / "dynawo.sh", "jobs", self.jobs_file],
                capture_output=not verbose,
                check=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            raise DynawoExecutionError("timeout")
        except subprocess.CalledProcessError as e:
            raise DynawoExecutionError(e.stderr) from e

    def read_output_curves(self):
        "Read curves outputted from Dynaωo simulation as pandas dataframe"
        curves = pd.read_csv(self.output_curves_path, sep=";")
        curves.set_index("time", inplace=True)
        # Dynawo output CSV ends lines with trailing ; so we drop the last column
        curves.drop(columns=[curves.columns[-1]], inplace=True)
        return curves

    def read_init_params(self):
        "If the simulation has been run with dumpInit, read the init params of all models"
        _init_params = defaultdict(dict)
        for dump_init_file in self.dump_init_folder.glob("**/*.txt"):
            model_name = dump_init_file.name.removesuffix(".txt").removeprefix(
                "dumpInitValues-"
            )
            with dump_init_file.open("r") as f:
                for line in f:
                    if "PARAMETERS VALUES" in line:
                        break
                for line in f:
                    if line.startswith(" ======"):
                        break
                    else:
                        name, value = line.split("=")
                        _init_params[model_name][name.strip()] = value.strip()
        return _init_params

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
        return self.__class__(
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
        except Exception:
            keep = True
            raise
        finally:
            if not keep:
                dup.delete()
