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
    parser.add_argument("-t", "--tag_prefix", default="")
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
        gen_all_curves_original(jobs_file_path, target, True)
    if gen_csv:
        start_time = datetime.datetime.now()
        os.system(dynawo_path + " jobs " + jobs_file_path)
        end_time = datetime.datetime.now()

        print("\nELAPSED TIME")
        print(end_time - start_time)
        print("\n\n\n")
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
    base_case_dir,
    jobs_file,
    curves_file,
    output_dir,
    dynawo_path,
    add_ini_par=False,
):
    output_jobs_file_path = output_dir + jobs_file

    # Copy the case to the output dir
    os.makedirs(output_dir, exist_ok=True)

    if base_case_dir != False:
        os.system("cp -rf {}* {}".format(base_case_dir, output_dir))

    allcurves_code.add_logs(output_jobs_file_path)

    # TODO: Check where to define this part
    # Delete namespaces tags
    os.system("""sed -i 's/<dyn:/</g' {} """.format(output_jobs_file_path))
    os.system("""sed -i 's/<\/dyn:/<\//g' {} """.format(output_jobs_file_path))
    os.system("""sed -i 's/:dyn//g' {} """.format(output_jobs_file_path))

    # TODO: Check if it's necessary
    # Modify the input curves file name
    if add_ini_par:
        allcurves_code.add_ini_par_file(output_jobs_file_path)
    allcurves_code.change_curve_file(output_jobs_file_path, curves_file)

    allcurves_code.add_precision_jobs_file(output_jobs_file_path)
    # Run case
    start_time = datetime.datetime.now()
    os.system(dynawo_path + " jobs " + output_jobs_file_path)
    end_time = datetime.datetime.now()
    print("\nELAPSED TIME")
    print(end_time - start_time)
    print("\n\n\n")

    logging.info("simulation end")


def replay(
    case_name,
    base_case_dir,
    jobs_file,
    terminals_csv,
    output_dir,
    dynawo_path,
    single_gen,
    tagPrefix,
):
    # TODO: Check if its necessary
    # os.makedirs(outdir + "/outputs", exist_ok=True)

    # Generate the replay files
    replay_code.gen_replay_files(base_case_dir, case_name, terminals_csv, output_dir, tagPrefix)

    if single_gen:
        replay_single_generators(case_name, output_dir, jobs_file, dynawo_path)
    else:
        run_simulation(output_dir + name + ".jobs", crvfile, "", dynawo_path, cd_dir=True)


def replay_single_generators(case_name, output_dir, jobs_file, dynawo_path):
    dydfile = output_dir + case_name + ".dyd"

    # TODO: Study what curves should be replayed
    crvfile_name = case_name + ".crv"
    crvfile = output_dir + crvfile_name
    # file = minidom.parse(dydfile)

    # TODO: Change this in order to replay only the needed gens
    # Get list of all generators of the dyd case file
    generators = replay_code.get_generators(dydfile, "dyn:")
    gen_ids = []
    for gen in generators:
        system = {}
        system["generators"] = {gen: generators[gen]}
        system["name"] = case_name
        gen_id = generators[gen]["dyd"].attributes["id"].value
        gen_ids.append(gen_id)

        output_dir_gen = output_dir + gen_id + "/"
        os.makedirs(output_dir_gen, exist_ok=True)
        os.system("cp {}/{} {}/".format(output_dir, jobs_file, output_dir_gen))
        os.system("cp {}/*.par {}/".format(output_dir, output_dir_gen))
        os.system("cp {}/*.crv {}/".format(output_dir, output_dir_gen))

        gen_dydfile = output_dir_gen + gen_id + ".dyd"
        gen_jobs_file_path = output_dir_gen + jobs_file

        # Create the single gen file
        replay_code.gen_dyd(system, gen_dydfile)

        allcurves_code.change_jobs_file(gen_jobs_file_path, gen_dydfile)

        run_simulation(False, jobs_file, crvfile, output_dir_gen, dynawo_path, True)

        logging.info("Replay generator " + gen_id)

    with open(output_dir + "generators.txt", "w") as f:
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


def calc_steady(time_values, curve_values, stable_time, ss_tol):

    # Get curves file and stable time

    if len(time_values) != len(curve_values):
        raise NameError("curve values and time values have different length")

    stable_time = float(stable_time)

    if stable_time <= 0:
        raise NameError("stable time is a non-valid value")

    # Get the first position of stable time in the dataframe
    time_pos = -1

    real_time = time_values[-1] - stable_time

    for i in range(len(time_values)):
        if real_time <= time_values[i]:
            time_pos = i
            break

    if time_pos == -1:
        raise NameError("stable time is bigger than simulation time")

    lst_val = curve_values[time_pos:]

    # If the value is less than 1, we use absolute value
    if abs(lst_val[-1]) <= 1:
        mean_val_max = lst_val[-1] + ss_tol
        mean_val_min = lst_val[-1] - ss_tol
    # If the value is more than 1, we use relative value
    else:
        mean_val = lst_val[-1]
        mean_val_max = mean_val + abs(ss_tol * mean_val)
        mean_val_min = mean_val - abs(ss_tol * mean_val)

    # Check all values inside the stable time
    stable = True
    for i in lst_val:
        if i < mean_val_min or i > mean_val_max:
            stable = False
            break

    first_stable = -1
    if stable:
        # Get the first position of the stabilization
        lst_val = curve_values
        first_stable = 0
        for i in range(len(lst_val)):
            pos = len(lst_val) - (i + 1)
            if lst_val[pos] < mean_val_min or lst_val[pos] > mean_val_max:
                first_stable = pos
                break

    # returns true if the stabilization is reached and returns its position in the given
    # lists
    return stable, curve_values[first_stable] if stable else 999999999


def get_metrics(values_1, times_1, values_2, times_2, ss_time, ss_tol):
    # Calc Time to steady
    stable1, TSS_1 = calc_steady(times_1, values_1, ss_time, ss_tol)
    stable2, TSS_2 = calc_steady(times_2, values_2, ss_time, ss_tol)

    TT = abs(TSS_1 - TSS_2)

    # Calc Diff peak to peak
    dPP = abs(abs(max(values_1) - min(values_1)) - abs(max(values_2) - min(values_2)))

    # Calc Diff steady state
    if stable1 and stable2:
        dSS = abs(values_1[-1] - values_2[-1])
    else:
        dSS = 999999999

    return TT, dPP, dSS


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

    dict_metrics = {"CurveName": [], "TT": [], "dPP": [], "dSS": []}
    for c in df2.columns:
        TT, dPP, dSS = get_metrics(list(df[c]), list(t), list(df2[c]), list(t2), 3, 0.005)

        plt.plot(t, df[c], label="original")
        plt.plot(t2, df2[c], label="replay", linestyle="--")
        plt.xlabel("Time (s)")
        plt.title(title + " " + c)
        plt.legend()
        plt.savefig(outputdir + "/" + c + ".png", dpi=300)
        plt.close("all")
        dict_metrics["CurveName"].append(c)
        dict_metrics["TT"].append(TT)
        dict_metrics["dPP"].append(dPP)
        dict_metrics["dSS"].append(dSS)

    df_metrics = pd.DataFrame.from_dict(dict_metrics)

    df_metrics.to_csv(outputdir + "../metrics.csv", sep=";")


def original_vs_replay_generators(original_csv, replay_dir):
    # Plot original and replayed curves for each generator in replay_dir
    with open(replay_dir + "/generators.txt") as file:
        generators = [line.rstrip() for line in file]
    for gen in generators:
        gen_dir = "{}/{}/".format(replay_dir, gen)
        fig_dir = gen_dir + "fig/"
        os.makedirs(fig_dir, exist_ok=True)
        with open(fig_dir + "vars.txt", "w") as f:
            f.write(gen + "\n")
        original_vs_replay(original_csv, gen_dir + "/outputs/curves/curves.csv", fig_dir, title="")


def runner(
    original_jobs_file_path,
    output_dir,
    dynawo_path,
    run_original,
    gen_crv,
    gen_csv,
    single_gen,
    tagPrefix,
):
    error = {}
    compression = {}

    # Get the case name
    case_name = subprocess.getoutput("basename " + original_jobs_file_path).split(".")[0]

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

    # Generate terminal curves file
    if gen_crv:
        if run_original:
            print("\nGenerating curves")
            os.makedirs(simulation_output_dir + "terminals/", exist_ok=True)
            allcurves_code.gen_all_curves_fast(
                case_name, base_case_dir, simulation_output_dir + "terminals/", False, tagPrefix
            )
            logging.info("generated .crv for all terminals")
        else:
            print("\nGenerating curves")
            os.makedirs(simulation_output_dir + "terminals/", exist_ok=True)
            allcurves_code.gen_all_curves_fast(
                case_name, base_case_dir, simulation_output_dir + "terminals/", True, tagPrefix
            )
            logging.info("generated .crv for all terminals")

    # Generate results csv terminal curves file
    if gen_csv:
        print("\nGenerating CSV with terminal curves")
        run_simulation(
            base_case_dir,
            jobs_file,
            case_name + "_terminals.crv",
            simulation_output_dir + "terminals/",
            dynawo_path,
            True,
        )
        logging.info("Generated CSV with terminal curves")

    # Define csv paths
    terminals_csv = simulation_output_dir + "/terminals/outputs/curves/curves.csv"
    replay_csv = simulation_output_dir + "/replay/outputs/curves/curves.csv"
    if run_original:
        original_csv = simulation_output_dir + "/terminals/outputs/curves/curves.csv"
    else:
        original_csv = None

    print("Plotting results")
    logging.info("Plotting results")

    # Reconstruction of the curves
    if single_gen:
        replay(
            case_name,
            base_case_dir,
            jobs_file,
            terminals_csv,
            simulation_output_dir + "replay/",
            dynawo_path,
            True,
            tagPrefix,
        )
        logging.info("Finished replay")

        if run_original:
            original_vs_replay_generators(original_csv, simulation_output_dir + "replay")
    """
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
            args.tag_prefix,
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
