# Dynaωo Replay - Curve Reconstruction

Dynaωo Replay is a tool designed for running dynamic power grid simulations using Dynaωo without the need to predefine export variables. With this tool, users can retrieve —reconstruct— specific curves afterward without re-running the entire simulation.

Curve reconstruction is performed using a technique we call ***local replay***. This involves creating an equivalent simulation to the original case, where only the element of interest is retained, and the rest of the network is replaced by an infinite bus that holds the boundary conditions observed during the original simulation.

To enable this reconstruction, the original simulation must store the boundary data required for the ***local replay***. These boundary data primarily include the voltage and frequency of the buses connected to the dynamic models (used later to create the infinite bus for the local replay) as well as other mandatory connection variables of the dynamic models. The process of running the original simulation while collecting all these data is referred to here as ***case preparation***.

Since the network in the ***local replay*** is trivial, its execution time is significantly shorter than re-running the original simulation. Additionally, the disk space required to store the data from the ***case preparation*** is (much) smaller than the space needed to save all possible variables from the original simulation.

This repository provides the `dynawo-replay` tool, which allows users to perform the ***case preparation*** and ***local replay*** steps for any Dynaωo case. These processes can be executed via the command line, as explained in this README, or programmatically, as demonstrated in the notebooks available in this repository.

## Installation
This tool is developed as a Python package. It can be installed using any `pip`-based installer. We recommend using `pipx` or `uv` to avoid dependency conflicts:

```sh
uv tool install git+https://github.com/dynawo/dynawo-replay-AIA
```

For analytical purposes, install the following version:

```sh
uv tool install git+https://github.com/dynawo/dynawo-replay-AIA[analytics]
```

But, of course, you can always go with plain `pip`:

```sh
pip install git+https://github.com/dynawo/dynawo-replay-AIA
```

Verify the installation with:

```sh
dynawo-replay --help
```

**Note:** This package relies on Dynaωo, which must be installed separately. See [Dynaωo installation docs](dynawo.com).

## Usage
The methodology consists of two main steps: case preparation and replay.

### Config
The path to the Dynaωo package used for running simulations is configured through the environment variable `DYNAWO_HOME`, which defaults to ```~/dynawo/```, but can be overridden via command-line options (see `--help` for each package command).

Other settings can also be configured via environment variables. See `src/dynawo_replay/config.py` for a complete list.

### Case preparation
Run the global simulation while storing necessary data for later curve reconstruction using the `prepare` command. Given a Dynaωo case located in `case/`, run:

```sh
dynawo-replay prepare case/
```

This executes the simulation using Dynaωo as defined in `case/`, exporting minimal variables and saving all required replay information in `case/replay/`.

### Replay
Reconstruct curves via a local replay. Provide the case folder, model ID, and the list of variables to be reconstructed using the `replay` command. For example:

```sh
dynawo-replay replay ./IEEE57_GeneratorDisconnection/ GEN____6_SM generator_iStatorPu_im generator_iStatorPu_re
```

For further details, use the `--help` option on any command.

## Caveats

This project is a proof of concept and is not yet a fully functional tool. The following limitations currently apply:
- Not all dynamic models are supported for local replay. Refer to the provided notebook for details on the criteria used to select supported models.
- The job file must contain only a single job.
- All dynamic models must be defined within a single DYD file.
- Parameters must be consolidated into a single PAR file, which must either have a `.par` extension or include `PAR` in its filename.
- Solver parameters may require manual tuning during the replay step.