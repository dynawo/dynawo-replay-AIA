import pytest

from dynawo_replay.config import settings
from dynawo_replay.schemas.curves_input import CurveInput
from dynawo_replay.simulation import Case

DYNAWO_EXAMPLES_FOLDER = settings.DYNAWO_HOME / "examples"


@pytest.mark.parametrize(
    "jobsfile",
    DYNAWO_EXAMPLES_FOLDER.glob("**/*.jobs"),
    ids=lambda jobsfile: str(jobsfile.relative_to(DYNAWO_EXAMPLES_FOLDER)),
)
def test_dynawo_examples(jobsfile):
    if "comparison" in jobsfile.parts:
        pytest.skip("Bad formatted case")
    try:
        with Case(jobsfile).replica() as case:
            case.run()
    except NotImplementedError:
        pytest.xfail("Not implemented")


def test_change_curves_to_output():
    with Case("data/IEEE57_Fault/IEEE57.jobs").replica() as case:
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
