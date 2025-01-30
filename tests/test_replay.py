from dynawo_replay.metrics import compare_curves
from dynawo_replay.schemas.curves_input import CurveInput
from dynawo_replay.simulation import Simulation


def test_replay_pipeline(tolerance=1e-2):
    with Simulation("data/IEEE14/IEEE14.jobs").replica() as case:
        case.generate_replayable_base(save=True)
        curves = [
            CurveInput(model="GEN____1_SM", variable="generator_iStatorPu_im"),
            CurveInput(model="GEN____1_SM", variable="generator_iStatorPu_re"),
            CurveInput(model="GEN____2_SM", variable="generator_iStatorPu_im"),
            CurveInput(model="GEN____3_SM", variable="generator_cePu"),
        ]
        case.crv.curve = curves
        case.save()
        case.run()
        original_df = case.read_output_curves()
        replayed_df = case.replay(curves)
        for curve in curves:
            column = f"{curve.model}_{curve.variable}"
            metrics = compare_curves(original_df[column], replayed_df[column])
            assert metrics.nrmse < tolerance
