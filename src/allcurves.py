import os, shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import subprocess
import logging, datetime
from xml.dom import minidom
from sklearn.utils.extmath import randomized_svd


def add_logs(jobsfilename, tagPrefix=""):
    file = minidom.parse(jobsfilename)
    logs = file.getElementsByTagName(tagPrefix + "logs")
    if logs:
        logs[0].parentNode.removeChild(logs[0])
    outputs = file.getElementsByTagName(tagPrefix + "outputs")[0]
    logs = file.createElement(tagPrefix + "logs")
    app1 = file.createElement(tagPrefix + "appender")
    app1.setAttribute("tag", "")
    app1.setAttribute("file", "dynawo.log")
    app1.setAttribute("lvlFilter", "DEBUG")
    app2 = file.createElement(tagPrefix + "appender")
    app2.setAttribute("tag", "VARIABLES")
    app2.setAttribute("file", "dynawoVariables.log")
    app2.setAttribute("lvlFilter", "DEBUG")
    logs.appendChild(app1)
    logs.appendChild(app2)
    outputs.appendChild(logs)
    with open(jobsfilename, "w") as out:
        # out.write(file.toprettyxml())
        file.writexml(out)
        out.close()


def compress_and_save(df, name, target="states", outpath="results", ranks=[10], randomized=True):
    df = np.array(df.iloc[:, 1:-1]).T
    error = []
    compression = []
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


def reconstruct_from_disk(name, target="states", path="results", ranks=[10]):
    reconstructed = []
    for r in ranks:
        filepath = "{}/{}/{}_{}_compressed_rank_{}.npy".format(path, name, name, target, r)
        with open(filepath, "rb") as f:
            u = np.load(f)
            d = np.load(f)
            v = np.load(f)
            fsize = os.path.getsize(filepath)
        reconstructed.append([np.dot(u, np.dot(np.diag(d), v)), [u, d, v], fsize])
    return reconstructed


def plot_results(df, dfsize, name, target="states", path="results", ranks=[10]):
    df = np.array(df.iloc[:, 1:-1]).T
    error = []
    compression = []
    os.makedirs("{}/{}".format(path, name), exist_ok=True)
    reconstructed = reconstruct_from_disk(name, target=target, ranks=ranks)
    for M_r, udv, fsize in reconstructed:
        u, d, v = udv
        r = d.size
        e = np.linalg.norm(df - M_r, ord="fro")
        c = fsize / dfsize
        compression.append(c)
        error.append(e)
        f, (ax1, ax2) = plt.subplots(2, 1)
        f.tight_layout(pad=2)
        np.random.RandomState(0)
        idx = np.random.permutation(np.arange(df.shape[0]))[0:60]
        ax1.plot(df[idx, :].T)
        ax1.set_title(name)
        # plt.savefig("plots/curves_{}.png".format(name))
        ax2.plot(M_r[idx, :].T)
        ax2.set_title("LRA  |  r = {}  |  c = {:0.4f}  |  e = {:0.4f}".format(r, c, e))
        plt.savefig(
            "{}/{}/{}_{}_curves_rank_{}.png".format(path, name, name, target, r),
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
            "{}/{}/{}_{}_rank_{}.png".format(path, name, name, target, r),
            dpi=300,
            bbox_inches="tight",
        )
        plt.close("all")
        plt.figure()
        plt.plot(d)
        plt.title(name)
        plt.savefig(
            "{}/{}/{}_{}_eigvals_{}.png".format(path, name, name, target, r),
            dpi=300,
            bbox_inches="tight",
        )
        plt.close("all")
    return error, compression


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


def add_ini_par_file(jobsfile, tag_prefix=""):
    file = minidom.parse(jobsfile)
    dumpInitValues = file.getElementsByTagName(tag_prefix + "dumpInitValues")
    if dumpInitValues:
        dumpInitValues = dumpInitValues[0]
        dumpInitValues.setAttribute("local", "true")
        dumpInitValues.setAttribute("global", "true")
    else:
        outputs = file.getElementsByTagName(tag_prefix + "outputs")[0]
        dumpInitValues = file.createElement(tag_prefix + "dumpInitValues")
        dumpInitValues.setAttribute("local", "true")
        dumpInitValues.setAttribute("global", "true")
        outputs.appendChild(dumpInitValues)

    with open(jobsfile, "w") as out:
        # out.write(file.toprettyxml())
        file.writexml(out)
        out.close()


def change_curve_file(jobsfile, curvefilename, tag_prefix=""):
    file = minidom.parse(jobsfile)
    curves = file.getElementsByTagName(tag_prefix + "curves")[0]
    curves.setAttribute("inputFile", curvefilename)
    with open(jobsfile, "w") as out:
        # out.write(file.toprettyxml())
        file.writexml(out)
        out.close()


def change_jobs_file(jobsfile, dydfilename, tag_prefix=""):
    file = minidom.parse(jobsfile)
    models = file.getElementsByTagName(tag_prefix + "dynModels")[0]
    models.setAttribute("dydFile", dydfilename)
    with open(jobsfile, "w") as out:
        # out.write(file.toprettyxml())
        file.writexml(out)
        out.close()


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

    output_jobs_file = case_dir + jobs_file

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


def gen_all_curves_fast(
    case_name,
    case_dir,
    output_dir,
    remove_previous,
):

    # Get generators of dyd file and create the new curves file

    dyd_path = case_dir + "/{}.dyd".format(case_name)
    dydfile = minidom.parse(dyd_path)

    blackBoxModel = dydfile.getElementsByTagName("dyn:blackBoxModel")

    model_gen_names = []

    for element in blackBoxModel:
        lib_name = element.getAttribute("lib")
        if lib_name[:9] == "Generator":
            model_gen_names.append(element.getAttribute("id"))

    # Modify original curves file
    crv_path = case_dir + "/{}.crv".format(case_name)
    crvfile = minidom.parse(crv_path)

    curvesInput = crvfile.getElementsByTagName("curvesInput")[0]
    if remove_previous:
        curves = curvesInput.getElementsByTagName("curve")
        for curve in curves:
            curve.parentNode.removeChild(curve)

    for gen_name in model_gen_names:
        gen_crv1 = crvfile.createElement("curve")
        gen_crv1.setAttribute("model", gen_name)
        gen_crv1.setAttribute("variable", "generator_terminal_V_im")
        curvesInput.appendChild(gen_crv1)

        gen_crv2 = crvfile.createElement("curve")
        gen_crv2.setAttribute("model", gen_name)
        gen_crv2.setAttribute("variable", "generator_terminal_V_re")
        curvesInput.appendChild(gen_crv2)

        gen_crv3 = crvfile.createElement("curve")
        gen_crv3.setAttribute("model", gen_name)
        gen_crv3.setAttribute("variable", "generator_terminal_i_im")
        curvesInput.appendChild(gen_crv3)

        gen_crv4 = crvfile.createElement("curve")
        gen_crv4.setAttribute("model", gen_name)
        gen_crv4.setAttribute("variable", "generator_terminal_i_re")
        curvesInput.appendChild(gen_crv4)

        gen_crv5 = crvfile.createElement("curve")
        gen_crv5.setAttribute("model", gen_name)
        gen_crv5.setAttribute("variable", "generator_omegaRefPu_value")
        curvesInput.appendChild(gen_crv5)

    crv_path_output = output_dir + "/{}_terminals.crv".format(case_name)
    # Write output without whitespaces
    with open(crv_path_output, "w") as out:
        xml_str = crvfile.toprettyxml()
        xml_str = os.linesep.join([s for s in xml_str.splitlines() if s != "	" and s])
        out.write(xml_str)
        out.close()

    logging.info("generated gen_all_curves_fast {}.crv".format(case_name))
