import os
import shutil
from pathlib import Path

from dynawo_replay import cli


def test_cli_run():
    jobs_file = Path("data/IEEE14/IEEE14.jobs")
    dynawo = Path("./vendor/dynawo-RTE_master_2022-11-03")
    cli.run(jobs_file=jobs_file, dynawo=dynawo, force=True)
    assert os.path.exists("data/IEEE14/replay")
    shutil.rmtree("data/IEEE14/replay")


def test_cli_full_pipeline():
    jobs_file = Path("data/IEEE14/IEEE14.jobs")
    dynawo = Path("./vendor/dynawo-RTE_master_2022-11-03")
    curves = [
        "GEN____1_SM::generator_iStatorPu_im",
        "GEN____1_SM::generator_iStatorPu_re",
        "GEN____2_SM::generator_iStatorPu_im",
        "GEN____3_SM::generator_cePu",
    ]
    cli.run(jobs_file=jobs_file, dynawo=dynawo, force=True)
    cli.replay(jobs_file=jobs_file, curves=curves, dynawo=dynawo)
    shutil.rmtree("data/IEEE14/replay")
