from dynawo_replay.schemas.curves_input import CurveInput
from dynawo_replay.simulation import Simulation


def test_IEEE14_Fault():
    with Simulation("data/IEEE14_Fault/IEEE14.jobs").replica() as case:
        case.run(verbose=True)


def test_IEEE57_Fault():
    with Simulation("data/IEEE57_Fault/IEEE57.jobs").replica() as case:
        case.run(verbose=True)


def test_change_curves_to_output():
    with Simulation("data/IEEE57_Fault/IEEE57.jobs").replica() as case:
        new_curves = [
            CurveInput(model="GEN____6_SM", variable="generator_terminal_i_re"),
            CurveInput(model="GEN____6_SM", variable="generator_omegaRefPu_value"),
            CurveInput(model="GEN____9_SM", variable="generator_terminal_V_im"),
            CurveInput(model="GEN____1_SM", variable="generator_terminal_V_im"),
            CurveInput(model="GEN___12_SM", variable="generator_terminal_V_im"),
            CurveInput(model="GEN___12_SM", variable="generator_terminal_i_re"),
        ]
        expected_columns = [f"{c.model}_{c.variable}" for c in new_curves]
        case.crv.curve = new_curves
        case.save()
        case.run()
        curves_df = case.read_output_curves()
        assert set(curves_df.columns) == set(expected_columns)
