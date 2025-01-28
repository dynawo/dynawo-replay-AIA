from dynawo_replay.simulation import Simulation


def test_IEEE57_Fault():
    with Simulation("data/IEEE57_Fault/IEEE57.jobs").duplicate() as case:
        case.run(verbose=True)


def test_generate_minimal_curves():
    with Simulation("data/IEEE57_Fault/IEEE57.jobs").duplicate() as case:
        minimal_curves = list(case.get_minimal_curves_for_replay())
        case.run(verbose=True)
        case.update_crv(minimal_curves)
        case.save()
        case.run()
        curves_df = case.read_output_curves()
        expected_columns = [f"{c.model}_{c.variable}" for c in minimal_curves]
        assert set(curves_df.columns) == set(expected_columns)
