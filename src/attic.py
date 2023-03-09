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
