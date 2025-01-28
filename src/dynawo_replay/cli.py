import datetime
import os
from pathlib import Path

import typer
from contexttimer import Timer
from rich.prompt import Confirm

from .config import settings
from .exceptions import CaseNotPreparedForReplay
from .schemas.curves_input import CurveInput
from .simulation import Simulation
from .simulator import runner

app = typer.Typer()


@app.command()
def run(jobs_file: str, dynawo: Path = settings.DYNAWO_HOME, keep_tmp: bool = False):
    """
    Executes a large-scale power grid simulation using Dynaωo,
    storing only the minimal data required to enable later reconstruction of curves.
    """
    case = Simulation(jobs_file, dynawo)
    output_folder = case.replayable_base_folder
    if output_folder.exists():
        continue_ = Confirm.ask(
            "Replay base folder for this case already exists and will be overwritten. "
            "Do you want to continue?"
        )
        if not continue_:
            return
    with Timer() as t:
        case.generate_replayable_base(keep_tmp=keep_tmp, save=True)
    typer.echo(f"Succesfully executed job «{case.job.name}» in {t.elapsed:.2}s.")
    typer.echo(f"Global output stored in {output_folder}.")


@app.command()
def replay(
    jobs_file: str,
    curves: list[str],
    dynawo: Path = settings.DYNAWO_HOME,
    keep_tmp: bool = False,
):
    """
    Reconstructs the desired variable curves for a specific simulation scenario
    by rerunning localized simulations with the previously stored minimal data.
    Curves must be passed in format {model}::{variable}.
    """
    parsed_curves = []
    for curve_str in sorted(curves):
        model, variable = curve_str.split("::")
        parsed_curves.append(CurveInput(model=model, variable=variable))
    with Timer() as t:
        case = Simulation(jobs_file, dynawo)
        try:
            df = case.replay(parsed_curves, keep_tmp=keep_tmp)
        except CaseNotPreparedForReplay:
            raise RuntimeError(
                "Case not prepared for replay. Execute ```run``` command first."
            )
        output_file = (
            case.base_folder
            / "replay"
            / f"replay_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        )
        df.to_csv(output_file, sep=";")
    typer.echo(f"Succesfully replayed curves {curves} in {t.elapsed:.2}s.")
    typer.echo(f"Output stored in {output_file}.")


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
