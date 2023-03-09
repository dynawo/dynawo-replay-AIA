import os
import datetime
import subprocess
import logging
import jinja2
import pandas as pd
import numpy as np
from matplotlib.pyplot import plt
from sklearn.utils.extmath import randomized_svd
import allcurves as allcurves_code


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
    reconstruct_from_disk(name, target, ranks=ranks)
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


def compress_and_save(df, name, target="states", outpath="results", ranks=[10], randomized=True):
    df = np.array(df.iloc[:, 1:-1]).T
    os.makedirs(outpath + "/" + name, exist_ok=True)
    for r in ranks:
        np.random.RandomState(1)
        f, (ax1, ax2) = plt.subplots(2, 1)
        f.tight_layout(pad=2)
        idx = np.random.permutation(np.arange(df.shape[0]))[0:60]
        ax1.plot(df[idx, :].T)
        ax1.set_title(name)
        # plt.savefig("plots/curves_{}.png".format(filename))
        if randomized:
            u, d, v = randomized_svd(df, r)
        else:
            u, d, v = np.linalg.svd(np.matrix(g(d[0:r]), v[0:r, :]))
        with open(
            outpath + "/{}/{}_{}_compressed_rank_{}.npy".format(name, name, target, r),
            "wb",
        ) as f:
            np.save(f, u)
            np.save(f, d)
            np.save(f, v)


def plot_svd(df, filename, ranks=[10], randomized=True):
    df = np.array(df.iloc[:, 1:-1]).T
    error = []
    compression = []
    os.makedirs("plots/" + filename, exist_ok=True)
    for r in ranks:
        np.random.RandomState(1)
        f, (ax1, ax2) = plt.subplots(2, 1)
        f.tight_layout(pad=2)
        idx = np.random.permutation(np.arange(df.shape[0]))[0:60]
        ax1.plot(df[idx, :].T)
        ax1.set_title(filename)
        # plt.savefig("plots/curves_{}.png".format(filename))
        if randomized:
            u, d, v = randomized_svd(df, r)
        else:
            u, d, v = np.linalg.svd(np.matrix(g(d[0:r]), v[0:r, :]))
        with open("results/{}/{}_compressed_rank_{}.npy".format(filename, filename, r)) as f:
            np.save(f, u)
            np.save(f, d)
            np.save(f, v)
        M_r = np.dot(u[:, 0:r], np.dot(np.diag(d[0:r]), v[0:r, :]))
        N, M = df.shape
        M_r_size = N * r + r + M * r
        c = M_r_size / (N * M)
        compression.append(c)
        e = np.linalg.norm(df - M_r, ord="fro")
        error.append(e)
        ax2.plot(M_r[idx, :].T)
        ax2.set_title("LRA  |  r = {}  |  c = {:0.4f}  |  e = {:0.4f}".format(r, c, e))
        plt.savefig(
            "results/{}/{}_curves_rank_{}.png".format(filename, filename, r),
            dpi=300,
            bbox_inches="tight",
        )
        plt.close("all")
        ##########
        f, (ax1, ax2) = plt.subplots(2, 1)
        f.tight_layout(pad=3)
        ax1.plot(u[:, 0:r])
        ax1.set_title("Top {} left SV".format(r))
        ax2.plot(v[0:r, :].T)
        ax2.set_title("Top {} right SV".format(r))
        plt.savefig(
            "results/{}/{}_rank_{}.png".format(filename, filename, r),
            dpi=300,
            bbox_inches="tight",
        )
        plt.close("all")
        plt.figure()
        plt.plot(d)
        plt.title(filename)
        plt.savefig(
            "results/{}/{}_eigvals_{}.png".format(filename, filename, r),
            dpi=300,
            bbox_inches="tight",
        )
        plt.close("all")
    return error, compression
    # M = np.array(df.iloc[:,1:-1])
    # Cxx = np.cov(M.T)
    # plt.imshow(Cxx)
    # plt.colorbar()
    # plt.savefig("plots/C_{}.png".format(filename))


def gen_all_curves_from_original(
    case_name,
    case_dir,
    output_dir,
    jobs_file,
    target="states",
    newvarlogs=False,
    recursive=True,
):
    # os.system("""egrep -rl '<dyn:' {}/ | xargs -I sed -i '' 's/<dyn:/</g'  """.format(dir))

    logfile = case_dir + "/outputs/logs/dynawoVariables.log"

    # Get data from output simulations
    os.system(
        """sed -n '/X variables$/,/alias/p' {} | sed 's/.* DEBUG | [0-9]\+ \\(.*\\)/\\1/p' >> {}/states.txt """.format(
            logfile, output_dir
        )
    )
    os.system(
        """ sed -n '/X variables$/,/alias/p' {} | sed '/terminal/!d' | sed 's/.* DEBUG | [0-9]\+ \\(.*\\)/\\1/p' >>  {}/terminals.txt """.format(
            logfile, output_dir
        )
    )
    os.system(
        """ sed -n '/X variables$/,/alias/p' {} | sed '/omegaRefPu/!d' | sed 's/.* DEBUG | [0-9]\+ \\(.*\\)/\\1/p' >>  {}/terminals.txt """.format(
            logfile, output_dir
        )
    )

    dydfile = case_dir + "/{}.dyd".format(case_name)
    os.system(
        """sed -n 's/.*id="\\([^"]*\\).*/\\1/p' {} > {}/models.txt """.format(dydfile, output_dir)
    )
    os.system("sh genallcrv.sh {}/models.txt {}/{}.txt".format(output_dir, output_dir, target))

    # Generate terminals crv fileyyy
    os.system("mv allcurves.crv {}/{}_{}.crv".format(output_dir, case_name, target))
    logging.info("generated allcurves_{}.crv".format(target))


def gen_crv(system, output):
    models = [x["dyd"] for x in system["generators"].values()]
    template_src = """<?xml version='1.0' encoding='UTF-8'?>
<!--
Copyright (c) 2022, RTE (http://www.rte-france.com)
See AUTHORS.txt
All rights reserved.
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, you can obtain one at http://mozilla.org/MPL/2.0/.
SPDX-License-Identifier: MPL-2.0

This file is part of Dynawo, an hybrid C++/Modelica open source suite of
simulation tools for power systems.
-->
<curvesInput xmlns="http://www.rte-france.com/dynawo">
    {% for model in models %}
    <curve model="{{model.attributes['id'].value}}" variable="generator_termina_V_re"/>
    <curve model="{{model.attributes['id'].value}}" variable="generator_termina_V_im"/>
    <curve model="{{model.attributes['id'].value}}" variable="generator_termina_I_re"/>
    <curve model="{{model.attributes['id'].value}}" variable="generator_termina_I_re"/>
    {% endfor %}
</curvesInput>
    """
    template = jinja2.Template(template_src)

    with open(output, "w") as f:
        f.write(template.render(models=models))


def remove_namespaces(file, tag):
    os.system("sed -i 's/<{}:/</g' {}".format(tag, file))
    os.system("sed -i 's/<\\/{}:/<\\//g' {}".format(tag, file))
