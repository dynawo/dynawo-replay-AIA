from pathlib import Path

from dynawo_replay.metrics import compare_curves
from dynawo_replay.replay import Replay
from dynawo_replay.schemas.curves_input import CurveInput
from dynawo_replay.simulation import Case


def test_replay_pipeline(tolerance=1e-2):
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
            assert metrics.nrmse < tolerance
