import os, shutil, jinja2
import pandas as pd
import numpy as np
import subprocess
import matplotlib.pyplot as plt
from xml.dom import minidom
import allcurves as allcurves_code
import replay as replay_code
import logging, datetime
from pathlib import Path
import matplotlib.pyplot as plt
import argparse


def parser_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("run_mode")
    parser.add_argument("root_dir")
    parser.add_argument("output_dir")
    parser.add_argument("dynawo_path")
    parser.add_argument("-r", "--run_original", action="store_true")
    parser.add_argument("-g", "--gen_crv", action="store_true")
    parser.add_argument("-c", "--gen_csv", action="store_true")
    parser.add_argument("-s", "--single_gen", action="store_true")

    args = parser.parse_args()
    return args


def compress_reconstruct(
    jobs_file_path,
    dynawo_path,
    ranks=[10],
    gen_curves=True,
    gen_csv=True,
    target="states",
):
    error = {}
    compression = {}
    print(jobs_file_path)
    name = subprocess.getoutput("basename " + jobs_file_path).split(".")[0]
    dir = subprocess.getoutput("dirname " + jobs_file_path)
    start = datetime.datetime.now()
    logging.info("\nExecution of " + jobs_file_path + " started at " + str(start))
    # begin pipeline execution
    print("\n***\n" + jobs_file_path + "\n***\n")

    if gen_curves:
        gen_all_curves(jobs_file_path, target, True)
    if gen_csv:
        os.system(dynawo_path + " jobs " + jobs_file_path)
        os.system(
            "mv {}/outputs/curves/curves.csv {}/outputs/curves/{}_curves.csv".format(
                dir, dir, target
            )
        )
        logging.info("finished Dynawo simulation")

    csvfile = dir + "/outputs/curves/{}_curves.csv".format(target)
    if not os.path.isfile(csvfile):
        logging.error(csvfile + " does not exist")
        return -1
    df = pd.read_csv(csvfile, sep=";")
    dfsize = os.path.getsize(csvfile)
    logging.info("read CSV")

    print("{} loaded".format(jobs_file_path))
    compress_and_save(df, name, target, ranks=ranks)
    logging.info("compressed matrix")
    reconstructed = reconstruct_from_disk(name, target, ranks=ranks)
    logging.info("reconstructed matrix")
    error[name], compression[name] = plot_results(df, dfsize, name, target, ranks=ranks)
    logging.info("plot results")
    # log finish
    end = datetime.datetime.now()
    elapsed = end - start
    logging.info(
        "Execution of "
        + jobs_file_path
        + " finished at "
        + str(end)
        + ". Time elapsed: "
        + str(elapsed)
        + "\n"
    )
    logging.info("\n")
    return error, compression


def run_simulation(
    case_name,
    base_case_dir,
    jobs_file,
    curves_file,
    output_dir,
    dynawo_path,
):
    output_jobs_file_path = output_dir + jobs_file

    # Copy the case to the output dir
    os.makedirs(output_dir, exist_ok=True)
    os.system("cp -rf {}* {}".format(base_case_dir, output_dir))

    allcurves_code.add_logs(output_jobs_file_path)

    # TODO: Check where to define this part
    # Delete namespaces tags
    os.system("""sed -i 's/<dyn:/</g' {} """.format(output_jobs_file_path))
    os.system("""sed -i 's/<\/dyn:/<\//g' {} """.format(output_jobs_file_path))
    os.system("""sed -i 's/:dyn//g' {} """.format(output_jobs_file_path))

    # TODO: Check if it's necessary
    # Modify the input curves file name
    allcurves_code.change_curve_file(output_jobs_file_path, curves_file)

    # Run case
    os.system(dynawo_path + " jobs " + output_jobs_file_path)

    logging.info("simulation end")


def replay(
    jobs_file_path, crvfile, terminals_csv, outdir, dynawo_path, single_gen=True
):
    name = subprocess.getoutput("basename " + jobs_file_path).split(".")[0]
    dir = subprocess.getoutput("dirname " + jobs_file_path) + "/"
    os.makedirs(outdir + "/outputs", exist_ok=True)
    gen_replay_files(dir, name, terminals_csv, outdir)
    outdir = os.path.abspath(outdir) + "/"
    if single_gen:
        replay_single_generators(name, outdir, dynawo_path)
    else:
        run_simulation(outdir + name + ".jobs", crvfile, "", dynawo_path, cd_dir=True)


def replay_single_generators(name, outdir, dynawo_path):
    dydfile = outdir + name + ".dyd"
    crvfile_name = name + ".crv"
    crvfile = outdir + crvfile_name
    file = minidom.parse(dydfile)
    generators = get_generators(dydfile)
    gen_ids = []
    for gen in generators:
        system = {}
        system["generators"] = {gen: generators[gen]}
        system["name"] = name
        gen_id = generators[gen]["dyd"].attributes["id"].value
        gen_ids.append(gen_id)
        gen_dydfile = outdir + "/" + gen_id + ".dyd"
        gen_jobs_file_path = outdir + name + ".jobs"
        gen_dyd(system, gen_dydfile)
        change_jobs_file(gen_jobs_file_path, gen_dydfile)
        run_simulation(
            gen_jobs_file_path, crvfile_name, outdir + gen_id, dynawo_path, cd_dir=True
        )
        logging.info("Replay generator " + gen_id)
    change_jobs_file(gen_jobs_file_path, name + ".dyd")
    with open(outdir + "generators.txt", "w") as f:
        f.write("\n".join(gen_ids))


def plot_csv(csvfile, outputfile, title="Simulation", num_curves=5):
    df = pd.read_csv(csvfile, sep=";")
    t = df.iloc[:, 0]
    df = df.iloc[:, 1:-1]
    N = df.shape[1]
    if num_curves:
        N = num_curves
    plt.plot(t, df.iloc[:, 0:N])
    plt.legend(df.columns[0:N])
    plt.xlabel("Time (s)")
    plt.title(title)
    plt.savefig(outputfile, dpi=300)
    plt.close("all")


def original_vs_replay(original_csv, replay_csv, outputdir, title="Simulation"):
    df = pd.read_csv(original_csv, sep=";")
    t = df.iloc[:, 0]
    df = df.iloc[:, 1:-1]
    df2 = pd.read_csv(replay_csv, sep=";")
    t2 = df2.iloc[:, 0]
    df2 = df2.iloc[:, 1:-1]
    with open(outputdir + "vars.txt", "a") as f:
        f.write(replay_csv + "\t")
        f.write("Original: {}, replay: {} \n".format(df.shape, df2.shape))
    for c in df2.columns:
        plt.plot(t, df[c], label="original")
        plt.plot(t2, df2[c], label="replay", linestyle="--")
        plt.xlabel("Time (s)")
        plt.title(title + " " + c)
        plt.legend()
        plt.savefig(outputdir + "/" + c + ".png", dpi=300)
        plt.close("all")


def original_vs_replay_generators(original_csv, replay_dir):
    """Plot original and replayed curves for each generator in replay_dir"""
    with open(replay_dir + "generators.txt") as file:
        generators = [line.rstrip() for line in file]
    for gen in generators:
        gen_dir = "{}/{}/".format(replay_dir, gen)
        fig_dir = replay_dir + "/fig/" + gen + "/"
        os.makedirs(fig_dir, exist_ok=True)
        with open(fig_dir + "vars.txt", "w") as f:
            f.write(gen + "\n")
        original_vs_replay(
            original_csv, gen_dir + "/outputs/curves/curves.csv", fig_dir, title=""
        )


def runner(
    original_jobs_file_path,
    output_dir,
    dynawo_path,
    run_original,
    gen_crv,
    gen_csv,
    single_gen,
):
    error = {}
    compression = {}

    # Get the case name
    case_name = subprocess.getoutput("basename " + original_jobs_file_path).split(".")[
        0
    ]

    # Get the base case directory name
    base_case_dir = subprocess.getoutput("dirname " + original_jobs_file_path) + "/"

    # Define the output directory
    simulation_output_dir = output_dir + "{}/".format(case_name)

    jobs_file = (
        case_name
        + "."
        + subprocess.getoutput("basename " + original_jobs_file_path).split(".")[-1]
    )

    os.makedirs(simulation_output_dir, exist_ok=True)

    # Create and config the simulation log file
    logging.basicConfig(
        filename=simulation_output_dir + "/simulation.log",
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=logging.DEBUG,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Begin pipeline execution
    start = datetime.datetime.now()
    logging.info("\nExecution of " + jobs_file + " started at " + str(start))

    print("\n***\n" + original_jobs_file_path + "\n***\n")

    # Run the original case
    if run_original:
        print("\nRunning original")
        run_simulation(
            case_name,
            base_case_dir,
            jobs_file,
            case_name + ".crv",
            simulation_output_dir + "original/",
            dynawo_path,
        )
        logging.info("Original simulation done")

    # Generate terminal curves file
    if gen_crv:
        print("\nGenerating curves")
        os.makedirs(simulation_output_dir + "terminals/", exist_ok=True)
        allcurves_code.gen_all_curves(
            case_name,
            simulation_output_dir + "original/",
            simulation_output_dir + "terminals/",
            jobs_file,
            "terminals",
            True,
        )
        logging.info("generated .crv for all terminals")

    # Generate results csv terminal curves file
    if gen_csv:
        print("\nGenerating CSV with terminal curves")
        run_simulation(
            case_name,
            base_case_dir,
            jobs_file,
            case_name + "_terminals.crv",
            simulation_output_dir + "terminals/",
            dynawo_path,
        )
        logging.info("Generated CSV with terminal curves")

    # Define csv paths
    print("\nReplaying")
    terminals_csv = simulation_output_dir + "/terminals/outputs/curves/curves.csv"
    original_csv = simulation_output_dir + "/original/outputs/curves/curves.csv"
    replay_csv = simulation_output_dir + "/replay/outputs/curves/curves.csv"

    print("Plotting results")
    logging.info("Plotting results")
    """
    if single_gen:
        replay(
            jobs_file_path,
            case_name + ".crv",
            terminals_csv,
            simulation_output_dir + "/replay/",
            dynawo_path,
            single_gen=True,
        )
        logging.info("Finished replay")
        original_vs_replay_generators(original_csv, simulation_output_dir + "/replay/")
    else:
        replay(
            jobs_file_path,
            case_name + ".crv",
            terminals_csv,
            simulation_output_dir + "/replay/",
            dynawo_path,
            single_gen=False,
        )
        logging.info("Finished replay")
        plot_csv(
            original_csv,
            simulation_output_dir + "{}_original.png".format(case_name),
            title=case_name + " Original",
        )
        plot_csv(
            replay_csv, simulation_output_dir + "{}_replay.png".format(case_name), title=case_name + " Replay"
        )
        original_vs_replay(
            original_csv, replay_csv, simulation_output_dir , title=case_name + " Original vs Replay"
        )
    return error, compression
"""


"""
root_dir = "examples_copy/DynaSwing"
# root_dir='../data/examples/DynaSwing/WSCC9/WSCC9_Fault/WSCC9.jobs'
root_dir = "../data/IEEE57/IEEE57_Fault/IEEE57.jobs"
# root_dir='../data/smallcase/IEEE57.jobs'
# root_dir='../data/FicheI3SM/FicheI3SM.jobs'
# root_dir='../data/Kundur_Example13/KundurExample13.jobs'
root_dir = "../data/examples/DynaSwing/IEEE14/IEEE14_Fault/IEEE14.jobs"
# root_dir='../data/TestCase3/TestCase3.jobs'
# root_dir='examples_copy/DynaSwing/GridForming_GridFollowing/DisconnectLine/'
# root_dir='../data/largecase/tFin/fic.jobs'
output_dir = "replay/"
"""

if __name__ == "__main__":
    args = parser_args()

    if str(args.run_mode) == "1":
        runner(
            os.path.abspath(args.root_dir),
            os.path.abspath(args.output_dir) + "/",
            os.path.abspath(args.dynawo_path),
            args.run_original,
            args.gen_crv,
            args.gen_csv,
            args.single_gen,
        )
    elif str(args.run_mode) == "3":
        compress_reconstruct(
            os.path.abspath(args.root_dir),
            os.path.abspath(args.dynawo_path),
            [10],
            args.gen_crv,
            args.gen_csv,
            "states",
        )
    else:
        print("run_mode must be 1 or 3")
