import datetime
from pathlib import Path

import typer
from contexttimer import Timer
from rich.prompt import Confirm

from .config import settings
from .exceptions import CaseNotPreparedForReplay
from .replay import ReplayableCase
from .utils import find_jobs_file

app = typer.Typer()


@app.command()
def prepare(
    case_folder: Path,
    dynawo: Path = settings.DYNAWO_HOME,
    keep_tmp: bool = False,
    keep_original_solver: bool = False,
    force: bool = False,
):
    """
    Executes a large-scale power grid simulation using Dynaωo,
    storing only the minimal data required to enable later reconstruction of curves.
    """
    jobs_file = find_jobs_file(case_folder)
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
        case.generate_replayable_base(
            keep_tmp=keep_tmp, keep_original_solver=keep_original_solver
        )
    typer.echo(f"Succesfully executed job «{case.name}» in {t.elapsed:.2}s.")
    typer.echo(f"Global output stored in {output_folder}.")


@app.command()
def replay(
    case_folder: Path,
    model_id: str,
    variables: list[str],
    dynawo: Path = settings.DYNAWO_HOME,
    apply_postprocessing: bool = settings.POSTPROCESS_ENABLED,
    keep_tmp: bool = False,
):
    """
    Reconstructs the desired variable curves for a specific simulation scenario
    by rerunning localized simulations with the previously stored minimal data.
    You must pass the case folder, the ID of model you want to replay, and the list of variables
    that you want to replay from this model.
    """
    with Timer() as t:
        jobs_file = find_jobs_file(case_folder)
        case = ReplayableCase(jobs_file, dynawo)
        try:
            df = case.replay(
                element_id=model_id,
                curves=variables,
                keep_tmp=keep_tmp,
                apply_postprocessing=apply_postprocessing,
            )
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
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, sep=";")
    typer.echo(f"Succesfully replayed {len(variables)} curves in {t.elapsed:.2}s.")
    typer.echo(f"Output stored in {output_file}.")
