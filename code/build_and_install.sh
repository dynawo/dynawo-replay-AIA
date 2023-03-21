#!/bin/bash
#
# Quick and dirty script to automate all steps for building/installing the package:
#   * it uses a venv named "dwo_venv" right under the top-level of the repo
#   * it also pip-updates all dependencies to their latest version ("eager" strategy)
# Assumes Python 3.4+.
# 
# (c) Grupo AIA / RTE
#     omsg@aia.es
#

# For saner programming:
set -o nounset -o noclobber
set -o errexit -o pipefail


PKG="dynawo_replay"
SCRIPT_PATH=$(realpath "$0")
MY_LOCAL_REPO=$(dirname "$SCRIPT_PATH")
MY_VENV="$MY_LOCAL_REPO"/dr_venv



GREEN="\\033[1;32m"
NC="\\033[0m"
colormsg()
{
    echo -e "${GREEN}$1${NC}"
}
colormsg_nnl()
{
    echo -n -e "${GREEN}$1${NC}"
}

help()
{
    echo "Usage: $0 [-e]"a
    echo
    echo " m     -e  editable_install"
}


# Process options
if [ $# -gt 1 ]; then
    help
    exit 1
fi
EDITABLE="N"
if [ $# = 1 ] && [ "$1" = "-e" ]; then
    EDITABLE="Y"
    colormsg "BUILDING & INSTALLING AN EDITABLE INSTALL"
fi


# Step 0: reminder to refresh your local workspace
echo "You're about to build & reinstall: $PKG  (remember to refresh your local repo if needed)"
read -p "Are you sure? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  exit
fi


# Step 1: make sure the Python venv exists and activate it
echo
if [ ! -d "$MY_VENV" ]; then
    colormsg_nnl "Virtual env not found, creating it now... "
    python3 -m venv "$MY_VENV"
    colormsg "OK."
fi
colormsg_nnl "Activating the venv... "
# shellcheck source=/dev/null
source "$MY_VENV"/bin/activate
colormsg "OK."
colormsg "Installing/upgrading pip & build in the venv... "
pip install --upgrade pip build
colormsg "OK."


# Step 2: build
echo
colormsg "Building the package... "
if [ $EDITABLE = "Y" ]; then
    colormsg "SKIPPING (editable install)."
else
    cd "$MY_LOCAL_REPO" && python3 -m build --wheel
    colormsg "OK."
fi

   
# Step 3: install the package
echo
colormsg "Installing the package... "
pip uninstall "$PKG"
if [ $EDITABLE = "Y" ]; then
    cd "$MY_LOCAL_REPO" && pip install -e .
else
    pip install "$MY_LOCAL_REPO"/dist/*.whl
fi
colormsg "OK."


# Step 4: upgrade all deps
echo
colormsg "Upgrading all dependencies... "
pip install -U --upgrade-strategy eager  "$PKG"
colormsg "OK."


# Step 5: install additional packages used only by developers
echo
colormsg "Installing developer utils... "
pip install -U --upgrade-strategy eager pytest
colormsg "OK."


# Step X: some packages do not automatically register their notebook extensions
# colormsg "Registering ipydatagrid as a Jupyter Notebook extension... "
# jupyter nbextension enable --py --sys-prefix ipydatagrid
# colormsg "Registering qgrid as a Jupyter Notebook extension... "
# jupyter nbextension enable --py --sys-prefix qgrid
# colormsg "OK. (to check all extensions, execute: jupyter nbextension list)"

