import os
import jinja2
import pandas as pd
import numpy as np
from xml.dom import minidom


# logging.basicConfig(
#     filename='replay.log',
#     format='%(asctime)s %(levelname)-8s %(message)s',
#     level=logging.INFO,
#     datefmt='%Y-%m-%d %H:%M:%S')


def get_tag_prefix(xml_file):
    # Get namespace
    tagPrefix = minidom._nssplit(xml_file.getElementsByTagName("*")[0].tagName)[0]

    if tagPrefix is None:
        tagPrefix = ""
    else:
        tagPrefix += ":"

    return tagPrefix


def gen_table(csvfile, output_dir):
    # Remove previous files
    if os.path.isfile(output_dir + "table.txt"):
        os.system("rm " + output_dir + "table.txt")

    # Create new table file
    df = pd.read_csv(csvfile, sep=";")
    time = df.iloc[:, 0]
    time = time - list(time)[0]
    # term_names = [x.split("_V_re")[0].replace(" ", "-") for x in df.columns[1:-1] if "V_re" in x]
    term_names = [x.split("_V_re")[0].replace(" ", " ") for x in df.columns[1:-1] if "V_re" in x]
    omega_names = [x.replace(" ", " ") for x in df.columns[1:-1] if "omega" in x]
    # omega_names = [x.replace(" ", "-") for x in df.columns[1:-1] if "omega" in x]
    with open(output_dir + "table.txt", "w") as f:
        f.write("#1\n")
        for omega in omega_names:
            Omg = df[omega]
            # f.write('#1\n double OmegaRefPu({},2)\n 0 1\n {} 1\n'.format(time.iloc[-1]))
            f.write("\ndouble {}({},2)\n".format(omega, len(Omg)))
            np.savetxt(f, np.array([time, Omg]).T, fmt="%.10f")
    with open(output_dir + "table.txt", "a") as f:
        for terminal in term_names:
            cols = df[[terminal + "_V_re", terminal + "_V_im"]]
            U = np.sqrt(cols[terminal + "_V_re"] ** 2 + cols[terminal + "_V_im"] ** 2)
            UPhase = np.arctan2(cols[terminal + "_V_im"], cols[terminal + "_V_re"])
            terminal = terminal.replace(" ", "-")  # need to remove spaces in column names in table
            f.write("\ndouble {}({},2)\n".format(terminal + "_U", len(U)))
            np.savetxt(f, np.array([time, U]).T, fmt="%.10f")
            f.write("\ndouble {}({},2)\n".format(terminal + "_UPhase", len(U)))
            np.savetxt(f, np.array([time, UPhase]).T, fmt="%.10f")
            # np.savetxt(f, df[["time",col]].values, fmt='%f')
    # shutil.copy(tablefile, output_dir+'table.txt')


def get_jobs_config(jobsfile):
    xml_file = minidom.parse(jobsfile)
    simulation = xml_file.getElementsByTagName("simulation")[0]
    system = {}
    system["simulation"] = {
        "startTime": str(0),
        "stopTime": str(
            float(simulation.attributes["stopTime"].value)
            - float(simulation.attributes["startTime"].value)
        ),
        "precision": simulation.attributes["precision"].value
        if "precision" in simulation.attributes
        else "1e-8",
    }
    return system


def get_generators(dydfile):
    xml_file = minidom.parse(dydfile)

    # Get namespace
    tagPrefix = get_tag_prefix(xml_file)

    models = xml_file.getElementsByTagName(tagPrefix + "blackBoxModel")
    generators = [x for x in models if "Generator" in x.attributes["lib"].value]
    gen_dict = {}
    for gen in generators:
        gen_dict[gen.attributes["id"].value] = {}
        gen_dict[gen.attributes["id"].value]["dyd"] = gen
    return gen_dict


def get_gen_params(parfile, models_dict):
    # name = subprocess.getoutput('basename '+jobsfile).split('.')[0]
    # dir = subprocess.getoutput('dirname '+jobsfile)
    xml_file = minidom.parse(parfile)

    # Get namespace
    tagPrefix = get_tag_prefix(xml_file)

    parsets = xml_file.getElementsByTagName(tagPrefix + "set")
    # iidmfile = dir+name+'.iidm'
    # add parset to each model
    for key, value in models_dict.items():
        id = value["dyd"].attributes["parId"].value
        params = [x for x in parsets if x.attributes["id"].value == id]
        if not params:
            print(id, "not found")
            print(value["dyd"].attributes["id"].value)
            continue
        params = params[0]
        params.setAttribute("dydId", value["dyd"].attributes["id"].value)  # set parId to id
        # get_refs(params, models_dict, iidmfile)
        models_dict[key]["par"] = params
    return models_dict


def get_solver_params(jobsfile, parfile, system):
    jobs = minidom.parse(jobsfile)
    par = minidom.parse(parfile)

    # Get namespace
    tagPrefix = get_tag_prefix(par)

    solver = jobs.getElementsByTagName("solver")[0]
    parsets = par.getElementsByTagName(tagPrefix + "set")
    system["solver"] = [
        x for x in parsets if solver.attributes["parId"].value == x.attributes["id"].value
    ][0]
    system["solver"].setAttribute("lib", solver.getAttribute("lib"))


def get_refs(generators, parsets, iidmfile):
    if not os.path.isfile(iidmfile):
        return 0
    iidm = minidom.parse(iidmfile)
    iidm_generators = iidm.getElementsByTagName("generator")
    if len(iidm_generators) == 0:
        iidm_generators = iidm.getElementsByTagName("iidm:generator")
    for s in parsets:
        refs = s.getElementsByTagName("reference")
        dyd_gen_id = [
            x["dyd"].attributes["id"].value
            for x in generators.values()
            if x["dyd"].attributes["parId"].value == s.attributes["id"].value
        ][0]
        gen = [
            x
            for x in iidm_generators
            if x.attributes["id"].value in dyd_gen_id or dyd_gen_id in x.attributes["id"].value
        ]
        if len(gen) == 0:
            print("Generator for references in set {} not found".format(s.attributes["id"].value))
            continue
        gen = gen[0]
        for r in refs:
            r_name = r.attributes["name"].value
            r.setAttribute("name", r_name)
            r.setAttribute("type", "DOUBLE")
            if "P0Pu" in r_name:
                r.setAttribute("value", str(float(gen.attributes["p"].value) / 100))
            elif "Q0Pu" in r_name:
                r.setAttribute("value", str(float(gen.attributes["q"].value) / 100))
            elif "U0Pu" in r_name:
                r.setAttribute(
                    "value",
                    str(
                        float(gen.attributes["targetV"].value)
                        / float(gen.parentNode.attributes["nominalV"].value)
                    ),
                )
            elif "UPhase0" in r_name:
                bus = [
                    x
                    for x in iidm.getElementsByTagName("iidm:bus")
                    if x.attributes["id"].value == gen.attributes["bus"].value
                ][0]
                r.setAttribute("value", str(float(bus.attributes["angle"].value) * (np.pi / 180)))


def gen_jobs(system, output):
    template_src = """<?xml version="1.0" ?><!--
Copyright (c) 2015-2020, RTE (http://www.rte-france.com)
See AUTHORS.txt
All rights reserved.
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, you can obtain one at http://mozilla.org/MPL/2.0/.
SPDX-License-Identifier: MPL-2.0

This file is part of Dynawo, an hybrid C++/Modelica open source time domain
simulation tool for power systems. -->
<jobs xmlns="http://www.rte-france.com/dynawo">
    <job name="{{system['name']}}">
        <solver lib="{{system['solver'].attributes['lib'].value}}" parFile="{{system['name']}}.par" parId="{{system['solver'].attributes['id'].value}}"/>-->
        <modeler compileDir="outputs/compilation">
            <!-- <network iidmFile="{{system['name']}}.iidm" parFile="{{system['name']}}.par" parId="Network"/> -->
            <dynModels dydFile="{{system['name']}}.dyd"/>
            <precompiledModels useStandardModels="true"/>
            <modelicaModels useStandardModels="true"/>
        </modeler>
        <simulation startTime="{{system['simulation']['startTime']}}" stopTime="{{system['simulation']['stopTime']}}" precision="{{system['simulation']['precision']}}"/>
        <outputs directory="outputs">
            <curves inputFile="{{system['name']}}.crv" exportMode="CSV"/>

            <logs><appender tag="" file="dynawo.log" lvlFilter="DEBUG"/><appender tag="VARIABLES" file="dynawoVariables.log" lvlFilter="DEBUG"/></logs></outputs>
    </job>
</jobs>
    """
    template = jinja2.Template(template_src)
    with open(output, "w") as f:
        f.write(template.render(system=system))


def gen_dyd(system, output, tagPrefix):
    models = [x["dyd"] for x in system["generators"].values()]
    template_src = (
        """<?xml version='1.0' encoding='UTF-8'?>
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
<"""
        + tagPrefix
        + """dynamicModelsArchitecture xmlns:dyn="http://www.rte-france.com/dynawo">
    {% for model in models %}
    <"""
        + tagPrefix
        + """blackBoxModel id="{{model.attributes['id'].value}}" lib="{{model.attributes['lib'].value}}" parFile="{{system['name']}}.par" parId="{{model.attributes['parId'].value}}"/>
    <"""
        + tagPrefix
        + """blackBoxModel id="IBus_{{model.attributes['id'].value}}" lib="InfiniteBusFromTable" parFile="{{system['name']}}.par" parId="IBus_{{model.attributes['id'].value}}"/>
    <"""
        + tagPrefix
        + """connect id1="{{model.attributes['id'].value}}" var1="generator_terminal" id2="IBus_{{model.attributes['id'].value}}" var2="infiniteBus_terminal"/>
    <"""
        + tagPrefix
        + """connect id1="{{model.attributes['id'].value}}" var1="generator_omegaRefPu_value" id2="IBus_{{model.attributes['id'].value}}" var2="infiniteBus_omegaRefPu"/>
    {% endfor %}
</"""
        + tagPrefix
        + """dynamicModelsArchitecture>
    """
    )
    template = jinja2.Template(template_src)
    with open(output, "w") as f:
        f.write(template.render(system=system, models=models))


def gen_par(system, output):
    parlist = [x["par"] for x in system["generators"].values()]
    template_src = """<?xml version="1.0" encoding="UTF-8"?>
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
<parametersSet xmlns="http://www.rte-france.com/dynawo">
  {% for modelpars in parlist -%}
  <set id="{{modelpars.attributes['id'].value}}" dydid="{{modelpars.attributes['dydId'].value}}">
    {% for param in modelpars.getElementsByTagName('par') -%}
    <par name="{{param.attributes['name'].value}}" type="{{param.attributes['type'].value}}" value="{{param.attributes['value'].value}}"/>  
    {% endfor -%}
    {% for param in modelpars.getElementsByTagName('reference') -%}
    <par name="{{param.attributes['name'].value}}" type="{{param.attributes['type'].value}}" value="{{param.attributes['value'].value}}"/>  
    {% endfor -%}
  </set>
  <set id="IBus_{{modelpars.attributes['dydId'].value}}">
    <par name="infiniteBus_UPuTableName"  type="STRING" value="{{modelpars.attributes['dydId'].value.replace(' ', '-')}}_generator_terminal_U"/>
    <par name="infiniteBus_UPhaseTableName" type="STRING" value="{{modelpars.attributes['dydId'].value.replace(' ', '-')}}_generator_terminal_UPhase"/>
    <par name="infiniteBus_OmegaRefPuTableName" type="STRING" value="{{modelpars.attributes['dydId'].value.replace(' ', '-')}}_generator_omegaRefPu_value"/>
    <par name="infiniteBus_TableFile" type="STRING" value="{{infinite_bus_table}}"/>
  </set>
  {% endfor -%}

   {{ system['solver'].toxml() }}

</parametersSet>
    """
    template = jinja2.Template(template_src)
    with open(output, "w") as f:
        f.write(
            template.render(
                system=system,
                parlist=parlist,
                infinite_bus_table=system["infinite_bus_table"],
            )
        )


def gen_par_IBus(system, output, parlist):

    xml_file = minidom.parse(output)
    parametersSet = xml_file.getElementsByTagName("parametersSet")[0]

    set_list = xml_file.getElementsByTagName("set")
    for modelpars in parlist:
        for set_elem in set_list:
            if set_elem.getAttribute("id") == modelpars.attributes["id"].value:
                set_elem.setAttribute("dydId", modelpars.attributes["dydId"].value)
                break

        IBus_par = xml_file.createElement("set")
        IBus_par.setAttribute("id", "IBus_" + modelpars.attributes["dydId"].value)

        par1 = xml_file.createElement("par")
        par2 = xml_file.createElement("par")
        par3 = xml_file.createElement("par")
        par4 = xml_file.createElement("par")

        par1.setAttribute("name", "infiniteBus_UPuTableName")
        par2.setAttribute("name", "infiniteBus_UPhaseTableName")
        par3.setAttribute("name", "infiniteBus_OmegaRefPuTableName")
        par4.setAttribute("name", "infiniteBus_TableFile")

        par1.setAttribute("type", "STRING")
        par2.setAttribute("type", "STRING")
        par3.setAttribute("type", "STRING")
        par4.setAttribute("type", "STRING")

        par1.setAttribute(
            "value",
            modelpars.attributes["dydId"].value.replace(" ", "-") + "_generator_terminal_U",
        )
        par2.setAttribute(
            "value",
            modelpars.attributes["dydId"].value.replace(" ", "-") + "_generator_terminal_UPhase",
        )
        par3.setAttribute(
            "value",
            modelpars.attributes["dydId"].value.replace(" ", "-") + "_generator_omegaRefPu_value",
        )
        par4.setAttribute("value", system["infinite_bus_table"])

        IBus_par.appendChild(par1)
        IBus_par.appendChild(par2)
        IBus_par.appendChild(par3)
        IBus_par.appendChild(par4)

        parametersSet.appendChild(IBus_par)

    # Write output without whitespaces
    with open(output, "w") as out:
        xml_str = xml_file.toprettyxml()
        xml_str = os.linesep.join(
            [
                s
                for s in xml_str.splitlines()
                if s != "	" and s and s != "		" and s != "    " and s != "  "
            ]
        )
        out.write(xml_str)
        out.close()


def solve_references(par_file, dumpinit_folder):
    xml_file = minidom.parse(par_file)
    reference_list = xml_file.getElementsByTagName("reference")

    for reference_elem in reference_list:
        if reference_elem.parentNode.hasAttribute("dydId"):
            atr_ref = reference_elem.getAttribute("name")
            value_ref = -9999999999
            with open(
                dumpinit_folder
                + "dumpInitValues-{}.txt".format(reference_elem.parentNode.getAttribute("dydId"))
            ) as f:
                for line in f:
                    line = line.rstrip()
                    if line[: len(atr_ref)] == atr_ref and line[len(atr_ref)] == " ":
                        value_ref = line.split("=")[1].replace(" ", "")
                        break
            if value_ref == -9999999999:
                print(reference_elem.parentNode.getAttribute("dydId"), atr_ref)
            par_ref = xml_file.createElement("par")
            par_ref.setAttribute("type", reference_elem.getAttribute("type"))
            par_ref.setAttribute("name", atr_ref)
            par_ref.setAttribute("value", str(value_ref))

            reference_elem.parentNode.appendChild(par_ref)
            reference_elem.parentNode.removeChild(reference_elem)

    # Write output without whitespaces
    with open(par_file, "w") as out:
        xml_str = xml_file.toprettyxml()
        xml_str = os.linesep.join(
            [
                s
                for s in xml_str.splitlines()
                if s != "	" and s and s != "		" and s != "    " and s != "  "
            ]
        )
        out.write(xml_str)
        out.close()


def gen_replay_files(root_dir, model, terminals_csv, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    # Generate the replay table file
    gen_table(terminals_csv, output_dir)

    in_jobs, in_par, in_dyd, in_iidm, in_crv = [
        root_dir + model + x for x in [".jobs", ".par", ".dyd", ".iidm", ".crv"]
    ]
    out_jobs, out_par, out_dyd, out_iidm, out_crv = [
        output_dir + model + x for x in [".jobs", ".par", ".dyd", ".iidm", ".crv"]
    ]

    # Get simulation config params
    system = get_jobs_config(in_jobs)

    # Get list of all dyd gens
    gen_dict = get_generators(in_dyd)

    # TODO: At the moment the original parameters are used, in
    # the future, to save memory, only the generator parameters
    # with these functions could be selected

    # Add gen initilization params
    get_gen_params(in_par, gen_dict)

    # Get initialization params that are defined in the iidm
    parlist = list(dict.fromkeys([x["par"] for x in gen_dict.values()]))

    # get_refs(gen_dict, parlist, root_dir + model + ".iidm")

    system["generators"] = gen_dict
    system["name"] = model
    system["infinite_bus_table"] = output_dir + "table.txt"

    # Get the solver parameters to use them in the recreation of the curves
    get_solver_params(in_jobs, in_par, system)

    # Generate the replay simulation files with all the data obtained above
    gen_jobs(system, out_jobs)

    gen_dyd(system, out_dyd, get_tag_prefix(minidom.parse(in_dyd)))
    os.system("cp '{}/{}.crv' '{}/{}.crv'".format(root_dir, model, output_dir, model))
    os.system("cp '{}/{}.par' '{}/{}.par'".format(root_dir, model, output_dir, model))
    # Add IBus to pars
    # gen_par(system, out_par)
    gen_par_IBus(system, out_par, parlist)
    solve_references(out_par, os.path.dirname(terminals_csv) + "/../initValues/globalInit/")

    # TODO: Study what curves should be replayed and modify this part

    return system
