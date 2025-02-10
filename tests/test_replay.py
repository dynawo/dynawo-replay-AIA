import random
from pathlib import Path

import numpy as np
import pytest

from dynawo_replay import Case, Replay, compare_curves, settings
from dynawo_replay.schemas.curves_input import CurveInput

DYNAWO_EXAMPLES_FOLDER = settings.DYNAWO_HOME / "examples"


def test_replay_pipeline():
    jobsfile = "data/IEEE14/IEEE14.jobs"
    dynawo = Path("./vendor/dynawo-RTE_master_2022-11-03")
    curves = [
        CurveInput(model="GEN____1_SM", variable="generator_iStatorPu_im"),
        CurveInput(model="GEN____1_SM", variable="generator_iStatorPu_re"),
        CurveInput(model="GEN____2_SM", variable="generator_iStatorPu_im"),
        CurveInput(model="GEN____3_SM", variable="generator_cePu"),
    ]
    with Case(jobsfile, dynawo=dynawo).replica() as case:
        replay = Replay(case)
        replay.generate_replayable_base(save=True)
        original_df = replay.calculate_reference_curves(curves)
        replayed_df = replay.replay(curves)
        for curve in curves:
            column = f"{curve.model}_{curve.variable}"
            metrics = compare_curves(original_df[column], replayed_df[column])
            assert metrics.nrmse < 100


@pytest.mark.parametrize(
    "jobsfile",
    DYNAWO_EXAMPLES_FOLDER.glob("**/*.jobs"),
    ids=lambda jobsfile: str(jobsfile.relative_to(DYNAWO_EXAMPLES_FOLDER)),
)
def test_replay_on_examples(jobsfile, random_seed=42, n_curves=1, tolerance=1):
    if "DynaFlow" in jobsfile.parts:
        pytest.skip("Skipping DynaFlow examples")
    try:
        with Case(jobsfile).replica() as case:
            if case.name in (
                # No generators found
                # "WECCWTG4A",
                # "WECCWTG4B",
                # "WECCPVVSource",
                # "WECCPV",
                # "WPP4ACurrentSource",
                # "WT4ACurrentSource",
                # "WPP4BCurrentSource",
                # "WT4BCurrentSource",
                # variables number 73 not equals to the equations number 74
                "Test Case 2 - Active power variation on the load",
                # time step <= 1e-06 s for more than 10 iterations
                "IEEE14 - Fault",
            ):
                pytest.skip("Manually skipped")
            replay = Replay(case)
            replay.generate_replayable_base(save=True)
            random.seed(random_seed)
            curves = random.sample(replay.list_all_possible_curves(), n_curves)
            original_df = replay.calculate_reference_curves(curves)
            replayed_df = replay.replay(curves)
            for curve in curves:
                column = f"{curve.model}_{curve.variable}"
                metrics = compare_curves(original_df[column], replayed_df[column])
                if not np.isnan(metrics.ptp_diff_rel):
                    assert metrics.ptp_diff_rel < tolerance
                if not np.isnan(metrics.ss_value_diff_rel):
                    assert metrics.ss_value_diff_rel < tolerance
                if not np.isnan(metrics.ss_time_diff):
                    assert metrics.ss_time_diff < 1
    except NotImplementedError:
        pytest.xfail("Not implemented")
