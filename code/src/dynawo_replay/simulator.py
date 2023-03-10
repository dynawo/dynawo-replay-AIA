import os
import datetime
import argparse
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
from xml.dom import minidom
from dynawo_replay import allcurves as allcurves_code
from dynawo_replay import replay as replay_code


def parser_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("root_dir")
    parser.add_argument("output_dir")
    parser.add_argument("dynawo_path")

    args = parser.parse_args()
    return args


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

    if base_case_dir is not False:
        os.system("cp -rf {}* {}".format(base_case_dir, output_dir))

    allcurves_code.add_logs(output_jobs_file_path)

    # Modify the input curves file name and add dumpInit
    if add_ini_par:
        allcurves_code.add_ini_par_file(output_jobs_file_path)
    allcurves_code.change_curve_file(output_jobs_file_path, curves_file)

    allcurves_code.add_precision_jobs_file(output_jobs_file_path)
    # Run case
    start_time = datetime.datetime.now()
    os.system(dynawo_path + ' jobs "' + output_jobs_file_path + '"')
    end_time = datetime.datetime.now()
    print("\nELAPSED TIME")
    print(end_time - start_time)
    print("\n\n\n")


def replay(
    case_name,
    base_case_dir,
    jobs_file,
    terminals_csv,
    output_dir,
    dynawo_path,
):
    # Generate the replay files
    replay_code.gen_replay_files(base_case_dir, case_name, terminals_csv, output_dir)

    replay_single_generators(case_name, output_dir, jobs_file, dynawo_path)


def replay_single_generators(case_name, output_dir, jobs_file, dynawo_path):
    dydfile = output_dir + case_name + ".dyd"
    crvfile_name = case_name + ".crv"
    crvfile = output_dir + crvfile_name

    # TODO: Change this in order to replay only the needed gens
    # Get list of all generators of the dyd case file
    generators = replay_code.get_generators(dydfile)
    gen_ids = []

    for gen in generators:
        system = {}
        system["generators"] = {gen: generators[gen]}
        system["name"] = case_name
        gen_id = generators[gen]["dyd"].attributes["id"].value
        gen_ids.append(gen_id)

        output_dir_gen = (output_dir + gen_id + "/").replace(" ", "_")
        os.makedirs(output_dir_gen, exist_ok=True)
        os.system("cp '{}/{}' '{}/'".format(output_dir, jobs_file, output_dir_gen))
        os.system("cp '{}/'*.par '{}/'".format(output_dir, output_dir_gen))
        os.system("cp '{}/'*.crv '{}/'".format(output_dir, output_dir_gen))

        gen_dydfile = output_dir_gen + gen_id + ".dyd"
        gen_jobs_file_path = output_dir_gen + jobs_file

        # Create the single gen file
        replay_code.gen_dyd(
            system, gen_dydfile, allcurves_code.get_tag_prefix(minidom.parse(dydfile))
        )

        allcurves_code.change_jobs_file(gen_jobs_file_path, gen_dydfile)
        run_simulation(False, jobs_file, crvfile, output_dir_gen, dynawo_path, True)

    with open(output_dir + "generators.txt", "w") as f:
        f.write("\n".join(gen_ids))


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
    return stable, time_values[first_stable] if stable else -999999999


def get_metrics(values_1, times_1, values_2, times_2, ss_time, ss_tol):
    # Calc Time to steady
    stable1, TSS_1 = calc_steady(times_1, values_1, ss_time, ss_tol)
    stable2, TSS_2 = calc_steady(times_2, values_2, ss_time, ss_tol)

    TT = abs(TSS_1 - TSS_2)

    # Calc Diff peak to peak
    PP_1 = abs(max(values_1) - min(values_1))
    PP_2 = abs(max(values_2) - min(values_2))
    dPP = abs(PP_1 - PP_2)

    # Calc Diff steady state
    if stable1 and stable2:
        SS_1 = values_1[-1]
        SS_2 = values_2[-1]
        dSS = abs(SS_1 - SS_2)
    else:
        SS_1 = -999999999
        SS_2 = -999999999
        dSS = -999999999

    return TT, TSS_1, TSS_2, dPP, PP_1, PP_2, dSS, SS_1, SS_2


def original_vs_replay(original_csv, replay_csv, outputdir, title="Simulation"):
    if (
        os.path.isfile(original_csv)
        and os.path.getsize(original_csv) > 0
        and os.path.isfile(replay_csv)
        and os.path.getsize(replay_csv) > 0
    ):
        df = pd.read_csv(original_csv, sep=";")
        t = df.iloc[:, 0]
        df = df.iloc[:, 1:-1]
        df2 = pd.read_csv(replay_csv, sep=";")
        t2 = df2.iloc[:, 0]
        df2 = df2.iloc[:, 1:-1]
        with open(outputdir + "vars.txt", "a") as f:
            f.write(replay_csv + "\t")
            f.write("Original: {}, replay: {} \n".format(df.shape, df2.shape))

        dict_metrics = {
            "CurveName": [],
            "TSS_Org": [],
            "TSS_Rep": [],
            "TT": [],
            "PP_Org": [],
            "PP_Rep": [],
            "dPP": [],
            "SS_Org": [],
            "SS_Rep": [],
            "dSS": [],
        }
        for c in df2.columns:
            TT, TSS_1, TSS_2, dPP, PP_1, PP_2, dSS, SS_1, SS_2 = get_metrics(
                list(df[c]), list(t), list(df2[c]), list(t2), 5, 0.002
            )

            plt.plot(t, df[c], label="original")
            plt.plot(t2, df2[c], label="replay", linestyle="--")
            plt.xlabel("Time (s)")
            plt.title(title + " " + c)
            plt.legend()
            plt.savefig(outputdir + "/" + c + ".png", dpi=300)
            plt.close("all")
            dict_metrics["CurveName"].append(c)
            dict_metrics["TSS_Org"].append(TSS_1)
            dict_metrics["TSS_Rep"].append(TSS_2)
            dict_metrics["TT"].append(TT)
            dict_metrics["PP_Org"].append(PP_1)
            dict_metrics["PP_Rep"].append(PP_2)
            dict_metrics["dPP"].append(dPP)
            dict_metrics["SS_Org"].append(SS_1)
            dict_metrics["SS_Rep"].append(SS_2)
            dict_metrics["dSS"].append(dSS)

        df_metrics = pd.DataFrame.from_dict(dict_metrics)

        df_metrics.to_csv(outputdir + "../metrics.csv", sep=";")
    else:
        print("No curves.csv file or no curves to compare in terminals or replay.")


def original_vs_replay_generators(original_csv, replay_dir):
    # Plot original and replayed curves for each generator in replay_dir
    with open(replay_dir + "/generators.txt") as file:
        generators = [line.rstrip() for line in file]
    for gen in generators:
        gen_dir = "{}/{}/".format(replay_dir, gen).replace(" ", "_")
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
):
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

    # Begin pipeline execution
    start = datetime.datetime.now()

    print("\n***\n" + original_jobs_file_path + "\n***\n")

    # Generate terminal curves file
    if gen_crv:
        if run_original:
            print("\nGenerating curves")
            os.makedirs(simulation_output_dir + "terminals/", exist_ok=True)
            allcurves_code.gen_all_curves_fast(
                case_name,
                base_case_dir,
                simulation_output_dir + "terminals/",
                False,
            )
        else:
            print("\nGenerating curves")
            os.makedirs(simulation_output_dir + "terminals/", exist_ok=True)
            allcurves_code.gen_all_curves_fast(
                case_name,
                base_case_dir,
                simulation_output_dir + "terminals/",
                True,
            )

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

    # Define csv paths
    terminals_csv = simulation_output_dir + "/terminals/outputs/curves/curves.csv"
    if run_original:
        original_csv = simulation_output_dir + "/terminals/outputs/curves/curves.csv"
    else:
        original_csv = None

    print("Plotting results")

    # Reconstruction of the curves
    replay(
        case_name,
        base_case_dir,
        jobs_file,
        terminals_csv,
        simulation_output_dir + "replay/",
        dynawo_path,
    )

    if run_original:
        original_vs_replay_generators(original_csv, simulation_output_dir + "replay")


def pipeline_validation():

    args = parser_args()

    runner(
        os.path.abspath(args.root_dir),
        os.path.abspath(args.output_dir) + "/",
        os.path.abspath(args.dynawo_path),
        True,
        True,
        True,
    )


def case_preparation():

    args = parser_args()

    runner(
        os.path.abspath(args.root_dir),
        os.path.abspath(args.output_dir) + "/",
        os.path.abspath(args.dynawo_path),
        True,
        True,
        True,
    )


def curves_creation():

    args = parser_args()

    runner(
        os.path.abspath(args.root_dir),
        os.path.abspath(args.output_dir) + "/",
        os.path.abspath(args.dynawo_path),
        True,
        True,
        True,
    )
