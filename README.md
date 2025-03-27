# Dynawo Replay - Curve Reconstruction

Dynawo Replay is a tool for running dynamic power grid simulations using Dynawo without predefining export variables. This allows users to extract additional variables afterward without re-running the entire simulation.

The methodology involves executing a global simulation while extracting only a minimal set of variables (curves). These are then used to recreate any desired variables via a *local replay*. In simplified terms, the simulation exports voltage and frequency at connection points of dynamic models (generators). The local replay then consists of a mini-simulation where the generator is connected to an infinite bus with voltage and frequency set to the extracted values from the global simulation.

## Installation
This tool is developed as a Python package and is available on PyPI. It can be installed using any `pip`-based installer. We recommend using `pipx` or `uv` to avoid dependency conflicts:

```sh
uv tool install git+https://github.com/dynawo/dynawo-replay-AIA
```

For analytical purposes, install the following version:

```sh
uv tool install git+https://github.com/dynawo/dynawo-replay-AIA[analytics]
```

Verify the installation with:

```sh
dynawo-replay --help
```

**Note:** This package relies on Dynawo, which must be installed separately. See [Dynawo installation docs](dynawo.com).

## Usage
The methodology consists of two main steps: case preparation and replay.

### Config
The path to the Dynawo package used for running simulations is configured through the environment variable ```DYNAWO_HOME```, which defaults to ```~/dynawo/```, but can be overridden via command-line options (see ```--help``` for each package command).

Other settings can also be configured via environment variables. See ```src/dynawo_replay/config.py``` for a complete list.

### Case preparation
Run the global simulation while storing necessary data for later curve reconstruction using the `prepare` command. Given a Dynawo case located in `case/`, run:

```sh
dynawo-replay prepare case/
```

This executes the simulation using Dynawo as defined in `case/`, exporting minimal variables and saving all required replay information in `case/replay/`.

### Replay
Reconstruct curves via a local replay. Provide the case folder, model ID, and the list of variables to be reconstructed using the `replay` command. For example:

```sh
dynawo-replay replay ./IEEE57_GeneratorDisconnection/ GEN____6_SM generator_iStatorPu_im generator_iStatorPu_re
```

For further details, use the `--help` option on any command.

