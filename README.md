# DynawoReplay
This repository contains the code for a software project that aims to execute contingencies of electrical power grids using the Dynawo simulator from RTE. The project allows for the execution of large power grid simulations and saving only the necessary information in the form of curves. This enables the creation of smaller simulations with detailed information (all the desired curves) without the overhead of executing the entire large case.

## How it Works
The software achieves this by creating small models using the full simulation that contain the generator from which information is required, and an infinite bus table representing the behavior of the network to which it is connected.

## Requirements
To run this software, you will need to have the following software installed:
- Dynawo simulator from RTE
- Python 3.x
- Pandas
- NumPy
- Jinja2
- Matplotlib
- Scikit-learn

## Installation
It is created using virtual environments with the aim of isolating the required packages in a clean environment free from dependency issues.
1. Clone this repository to your local machine
2. Install Dynawo simulator from RTE
3. Run the build_and_install.sh script to create the virtual environment and download the necessary dependencies.

## Usage
1. Obtain the electrical power grid model to work with.
2. Activate the virtual environment with:
```
source dr_venv/bin/activate
```
3. Execute one of the desired commands with the data from the original case:
```
pipeline_validation [-h] jobs_path output_dir dynawo_path
```
(it is used to make a complete validation of the software and all the case generators, obtaining graphs and metrics)
```
case_preparation [-h] jobs_path output_dir dynawo_path
```
(it is used to prepare a case for later replay)
```
curves_creation [-h] jobs_path output_dir dynawo_path curves_file [replay_generators]
```
(it is used to obtain the curves of a case already prepared from one, several or all of its generators)
