import os
import shutil
from pathlib import Path

from dynawo_replay import cli


def test_cli_run():
    case_folder = Path("data/IEEE14/")
    dynawo = Path("./vendor/dynawo-RTE_master_2022-11-03")
    cli.prepare(case_folder=case_folder, dynawo=dynawo, force=True)
    assert os.path.exists("data/IEEE14/replay")
    shutil.rmtree("data/IEEE14/replay")


def test_cli_full_pipeline():
    case_folder = Path("data/IEEE14/")
    dynawo = Path("./vendor/dynawo-RTE_master_2022-11-03")
    model_id = "GEN____1_SM"
    variables = ["generator_iStatorPu_im", "generator_iStatorPu_re"]
    cli.prepare(case_folder=case_folder, dynawo=dynawo, force=True)
    cli.replay(
        case_folder=case_folder, model_id=model_id, variables=variables, dynawo=dynawo
    )
    shutil.rmtree("data/IEEE14/replay")
