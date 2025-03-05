import random
from pathlib import Path

import numpy as np
import pytest

from dynawo_replay import ReplayableCase, compare_curves, settings
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
    with ReplayableCase(jobsfile, dynawo=dynawo).replica() as case:
        case.generate_replayable_base()
        original_df = case.calculate_reference_curves(curves)
        replayed_df = case.replay(curves)
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
    try:
        with ReplayableCase(jobsfile).replica() as case:
            all_possible_curves = [
                CurveInput(model=el.id, variable=v.name)
                for el in case.replayable_elements.values()
                for v in el.replayable_variables
            ]
            if not all_possible_curves:
                pytest.skip("No replayable elements")
            random.seed(random_seed)
            curves_to_replay = random.sample(all_possible_curves, n_curves)
            case.generate_replayable_base()
            original_df = case.calculate_reference_curves(curves_to_replay)
            replayed_df = case.replay(curves_to_replay)
            for curve in curves_to_replay:
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
