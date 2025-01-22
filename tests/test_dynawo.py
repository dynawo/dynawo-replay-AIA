from dynawo_replay.simulation import Simulation


def test_IEEE57_Fault():
    case = Simulation("data/IEEE57_Fault/IEEE57.jobs").duplicate()
    case.run(verbose=True)
    case.delete()


def test_generate_minimal_curves():
    case = Simulation("data/IEEE57_Fault/IEEE57.jobs").duplicate()
    minimal_curves = list(case.get_minimal_curves_for_replay())
    case.update_crv(minimal_curves)
    case.save()
    case.run()
    curves_df = case.read_curves()
    expected_columns = [f"{c.model}_{c.variable}" for c in minimal_curves]
    assert set(curves_df.columns) == set(expected_columns)
    case.delete()
