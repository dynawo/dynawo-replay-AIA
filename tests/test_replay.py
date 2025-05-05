from dynawo_replay import ReplayableCase
from dynawo_replay.metrics import compare_curves


def test_replay_ieee14():
    with ReplayableCase("tests/data/IEEE14/IEEE14.jobs").replica() as case:
        element = "GEN____1_SM"
        curves = ["generator_PGenPu", "generator_IRotorPu_value"]
        case.generate_replayable_base()
        replayed_df = case.replay(element, curves)
        reference_df = case.calculate_reference_curves(element, curves)
        for curve in curves:
            column = f"{element}_{curve}"
            compare_curves(reference_df[column], replayed_df[column])


def test_replay_ieee57():
    with ReplayableCase("tests/data/IEEE57/IEEE57.jobs").replica() as case:
        element = "GEN___12_SM"
        curves = ["generator_cos2Eta"]
        case.generate_replayable_base()
        replayed_df = case.replay(element, curves)
        reference_df = case.calculate_reference_curves(element, curves)
        for curve in curves:
            column = f"{element}_{curve}"
            compare_curves(reference_df[column], replayed_df[column])


def test_replay_ieee118():
    with ReplayableCase("tests/data/IEEE118/IEEE118.jobs").replica() as case:
        element = "B1-G1"
        curves = ["generator_Ce0Pu", "generator_LambdaAD0Pu", "generator_MdSat0PPu"]
        case.generate_replayable_base()
        replayed_df = case.replay(element, curves)
        reference_df = case.calculate_reference_curves(element, curves)
        for curve in curves:
            column = f"{element}_{curve}"
            compare_curves(reference_df[column], replayed_df[column])
