import os
import numpy as np
import matplotlib.pyplot as plt
import logging
from xml.dom import minidom
from xml import sax


def get_tag_prefix(xml_file):
    # Get namespace
    tagPrefix = minidom._nssplit(xml_file.getElementsByTagName("*")[0].tagName)[0]

    if tagPrefix is None:
        tagPrefix = ""
    else:
        tagPrefix += ":"

    return tagPrefix


def add_logs(jobsfilename):
    xml_file = minidom.parse(jobsfilename, sax.make_parser())

    # Get namespace
    tagPrefix = get_tag_prefix(xml_file)

    logs = xml_file.getElementsByTagName(tagPrefix + "logs")
    if logs:
        logs[0].parentNode.removeChild(logs[0])
    outputs = xml_file.getElementsByTagName(tagPrefix + "outputs")[0]
    logs = xml_file.createElement(tagPrefix + "logs")
    app1 = xml_file.createElement(tagPrefix + "appender")
    app1.setAttribute("tag", "")
    app1.setAttribute("file", "dynawo.log")
    app1.setAttribute("lvlFilter", "DEBUG")
    app2 = xml_file.createElement(tagPrefix + "appender")
    app2.setAttribute("tag", "VARIABLES")
    app2.setAttribute("file", "dynawoVariables.log")
    app2.setAttribute("lvlFilter", "DEBUG")
    logs.appendChild(app1)
    logs.appendChild(app2)
    outputs.appendChild(logs)
    with open(jobsfilename, "w") as out:
        # out.write(xml_file.toprettyxml())
        xml_file.writexml(out)
        out.close()


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


def add_ini_par_file(jobsfile):
    xml_file = minidom.parse(jobsfile)

    # Get namespace
    tagPrefix = get_tag_prefix(xml_file)

    dumpInitValues = xml_file.getElementsByTagName(tagPrefix + "dumpInitValues")
    if dumpInitValues:
        dumpInitValues = dumpInitValues[0]
        dumpInitValues.setAttribute("local", "false")
        dumpInitValues.setAttribute("global", "true")
    else:
        outputs = xml_file.getElementsByTagName(tagPrefix + "outputs")[0]
        dumpInitValues = xml_file.createElement(tagPrefix + "dumpInitValues")
        dumpInitValues.setAttribute("local", "false")
        dumpInitValues.setAttribute("global", "true")
        outputs.appendChild(dumpInitValues)

    with open(jobsfile, "w") as out:
        # out.write(xml_file.toprettyxml())
        xml_file.writexml(out)
        out.close()


def add_precision_jobs_file(jobsfile):
    xml_file = minidom.parse(jobsfile)
    simulation = xml_file.getElementsByTagName("simulation")[0]
    system = {}

    if "precision" not in simulation.attributes:
        simulation.setAttribute("precision", "1e-8")

    with open(jobsfile, "w") as out:
        # out.write(xml_file.toprettyxml())
        xml_file.writexml(out)
        out.close()

    return system


def change_curve_file(jobsfile, curvefilename):
    xml_file = minidom.parse(jobsfile)

    # Get namespace
    tagPrefix = get_tag_prefix(xml_file)

    curves = xml_file.getElementsByTagName(tagPrefix + "curves")[0]
    curves.setAttribute("inputFile", curvefilename)
    with open(jobsfile, "w") as out:
        # out.write(xml_file.toprettyxml())
        xml_file.writexml(out)
        out.close()


def change_jobs_file(jobsfile, dydfilename):
    xml_file = minidom.parse(jobsfile)

    # Get namespace
    tagPrefix = get_tag_prefix(xml_file)

    models = xml_file.getElementsByTagName(tagPrefix + "dynModels")[0]
    models.setAttribute("dydFile", dydfilename)
    with open(jobsfile, "w") as out:
        # out.write(xml_file.toprettyxml())
        xml_file.writexml(out)
        out.close()


def gen_all_curves_fast(
    case_name,
    case_dir,
    output_dir,
    remove_previous,
):

    # Get generators of dyd file and create the new curves file

    dyd_path = case_dir + "/{}.dyd".format(case_name)
    dydfile = minidom.parse(dyd_path)

    # Get namespace
    tagPrefix = get_tag_prefix(dydfile)

    blackBoxModel = dydfile.getElementsByTagName(tagPrefix + "blackBoxModel")
    if len(blackBoxModel) == 0:
        print(
            "No generators found in the model. Please, check if the file tags have any prefix (dyn:), and provide it through the options."
        )
        exit()

    model_gen_names = [
        element.getAttribute("id")
        for element in blackBoxModel
        if "Generator" in element.attributes["lib"].value
    ]

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
