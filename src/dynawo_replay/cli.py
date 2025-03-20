import datetime
from pathlib import Path

import typer
from contexttimer import Timer
from rich.prompt import Confirm

from .config import settings
from .exceptions import CaseNotPreparedForReplay
from .replay import ReplayableCase
from .schemas.curves_input import CurveInput

app = typer.Typer()


@app.command()
def prepare(
    jobs_file: Path,
    dynawo: Path = settings.DYNAWO_HOME,
    keep_tmp: bool = False,
    force: bool = False,
):
    """
    Executes a large-scale power grid simulation using Dynaωo,
    storing only the minimal data required to enable later reconstruction of curves.
    """
    case = ReplayableCase(jobs_file, dynawo)
    output_folder = case.replay_core_folder
    if output_folder.exists() and not force:
        continue_ = Confirm.ask(
            "Replay base folder for this case already exists and will be overwritten. "
            "Do you want to continue?"
        )
        if not continue_:
            return
    with Timer() as t:
        case.generate_replayable_base(keep_tmp=keep_tmp, save=True)
    typer.echo(f"Succesfully executed job «{case.name}» in {t.elapsed:.2}s.")
    typer.echo(f"Global output stored in {output_folder}.")


@app.command()
def replay(
    jobs_file: Path,
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
        case = ReplayableCase(jobs_file, dynawo)
        try:
            df = case.replay(parsed_curves, keep_tmp=keep_tmp)
        except CaseNotPreparedForReplay:
            raise RuntimeError(
                "Case not prepared for replay. Execute ```run``` command first."
            )
        output_file = (
            case.base_folder
            / "replay"
            / "outputs"
            / f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        )
        df.to_csv(output_file, sep=";")
    typer.echo(f"Succesfully replayed curves {curves} in {t.elapsed:.2}s.")
    typer.echo(f"Output stored in {output_file}.")
