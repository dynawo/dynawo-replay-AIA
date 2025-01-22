import os

import typer

from .simulator import runner

app = typer.Typer()


@app.command()
def run(jobs_file: str):
    """
    Executes a large-scale power grid simulation using Dynawo,
    storing only the minimal data required to enable later reconstruction of curves.
    """
    # create the Simulation instance with the folder given
    # calculate the curves needed to simulate
    # add the curves into to job
    # run the job
    # (maybe) compress the final output
    pass


@app.command()
def replay(jobs_file: str, curves: list[str]):
    """
    Reconstructs the desired variable curves for a specific simulation scenario
    by rerunning localized simulations with the previously stored minimal data.
    """
    # go to the case folder
    # build the new Simulation instance with the output
    # run the new simulation
    pass


@app.command()
def pipeline_validation(jobs_path: str, output_dir: str, dynawo_path: str):
    typer.echo(f"Running pipeline_validation {jobs_path}, {output_dir}, {dynawo_path}")
    runner(
        os.path.abspath(jobs_path),
        os.path.abspath(output_dir) + "/",
        os.path.abspath(dynawo_path),
        None,
        ["ALL"],
        True,
        True,
        True,
        True,
        None,
        None,
    )


@app.command()
def case_preparation(jobs_path: str, output_dir: str, dynawo_path: str):
    typer.echo(f"Running case_preparation {jobs_path}, {output_dir}, {dynawo_path}")
    runner(
        os.path.abspath(jobs_path),
        os.path.abspath(output_dir) + "/",
        os.path.abspath(dynawo_path),
        None,
        [],
        True,
        True,
        True,
        False,
        None,
        None,
    )


@app.command()
def curves_creation(
    jobs_path: str,
    output_dir: str,
    dynawo_path: str,
    curves_file: str,
    replay_generators: list[str] = ["ALL"],
):
    typer.echo(
        f"Running curves_creation {jobs_path}, {output_dir}, {dynawo_path}, {curves_file}, {replay_generators}"
    )
    runner(
        os.path.abspath(jobs_path),
        os.path.abspath(output_dir) + "/",
        os.path.abspath(dynawo_path),
        os.path.abspath(curves_file),
        replay_generators,
        False,
        False,
        False,
        True,
        None,
        None,
    )


@app.command()
def get_value(
    jobs_path: str,
    output_dir: str,
    dynawo_path: str,
    curves_file: str,
    replay_generator: str,
    value_name: str,
    time_get_value: str,
):
    typer.echo(
        f"Running get_value {jobs_path}, {output_dir}, {dynawo_path}, "
        f"{curves_file}, {replay_generator}, {value_name}, {time_get_value}"
    )
    runner(
        os.path.abspath(jobs_path),
        os.path.abspath(output_dir) + "/",
        os.path.abspath(dynawo_path),
        os.path.abspath(curves_file),
        [replay_generator],
        False,
        False,
        False,
        True,
        value_name,
        float(time_get_value),
    )
