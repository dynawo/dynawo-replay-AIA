import os
import shutil
from pathlib import Path

from dynawo_replay import cli


def test_cli_run_ieee14():
    case_folder = Path("tests/data/IEEE14/")
    cli.prepare(case_folder=case_folder, force=True)
    assert os.path.exists("tests/data/IEEE14/replay")
    shutil.rmtree("tests/data/IEEE14/replay")


def test_cli_full_pipeline_ieee14():
    case_folder = Path("tests/data/IEEE14/")
    model_id = "GEN____1_SM"
    variables = ["generator_PGenPu", "generator_QGen"]
    cli.prepare(case_folder=case_folder, force=True)
    cli.replay(case_folder=case_folder, model_id=model_id, variables=variables)
    shutil.rmtree("tests/data/IEEE14/replay")
