from dynawo_replay.cli import case_preparation, pipeline_validation


def test_case_preparation():
    case_preparation(
        "data/tmp/IEEE57_Fault/IEEE57.jobs",
        "data/tmp/output/",
        "./vendor/dynawo-RTE_master_2022-11-03/dynawo.sh",
    )


def test_pipeline_validation():
    pipeline_validation(
        "data/tmp/IEEE57_Fault/IEEE57.jobs",
        "data/tmp/output/",
        "./vendor/dynawo-RTE_master_2022-11-03/dynawo.sh",
    )


# def test_curves_creation():
#     curves_creation(
#         "data/tmp/tmp4saw8cag/IEEE57.jobs",
#         "data/tmp/output/",
#         "./vendor/dynawo-RTE_master_2022-11-03/dynawo.sh",
#     )


# def test_get_value():
#     get_value(
#         "data/tmp/tmp4saw8cag/IEEE57.jobs",
#         "data/tmp/output/",
#         "./vendor/dynawo-RTE_master_2022-11-03/dynawo.sh",
#     )
