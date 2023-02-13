import os, shutil, jinja2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from xml.dom import minidom
from allcurves import *
import logging, datetime

# logging.basicConfig(
#     filename='replay.log',
#     format='%(asctime)s %(levelname)-8s %(message)s',
#     level=logging.INFO,
#     datefmt='%Y-%m-%d %H:%M:%S')


def gen_table(csvfile, output_dir):
    os.system("rm " + output_dir + "table.txt")
    df = pd.read_csv(csvfile, sep=";")
    time = df.iloc[:, 0]
    term_names = [x.split("_V_re")[0].replace(" ", "-") for x in df.columns[1:-1] if "V_re" in x]
    omega_names = [x.replace(" ", "-") for x in df.columns[1:-1] if "omega" in x]
    with open(output_dir + "table.txt", "w") as f:
        f.write("#1\n")
        for omega in omega_names:
            O = df[omega]
            # f.write('#1\n double OmegaRefPu({},2)\n 0 1\n {} 1\n'.format(time.iloc[-1]))
            f.write("\ndouble {}({},2)\n".format(omega, len(O)))
            np.savetxt(f, np.array([time, O]).T, fmt="%.10f")
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
    file = minidom.parse(jobsfile)
    simulation = file.getElementsByTagName("simulation")[0]
    system = {}
    system["simulation"] = {
        "startTime": simulation.attributes["startTime"].value,
        "stopTime": simulation.attributes["stopTime"].value,
    }
    return system


def get_generators(dydfile, tagPrefix="dyn:"):
    file = minidom.parse(dydfile)
    models = file.getElementsByTagName(tagPrefix + "blackBoxModel")
    generators = [x for x in models if "Generator" in x.attributes["lib"].value]
    gen_dict = {}
    for gen in generators:
        gen_dict[gen.attributes["id"].value] = {}
        gen_dict[gen.attributes["id"].value]["dyd"] = gen
    return gen_dict


def get_gen_params(parfile, models_dict, tagPrefix=""):
    # name = subprocess.getoutput('basename '+jobsfile).split('.')[0]
    # dir = subprocess.getoutput('dirname '+jobsfile)
    file = minidom.parse(parfile)
    parsets = file.getElementsByTagName(tagPrefix + "set")
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


def get_solver_params(jobsfile, parfile, system, tagPrefix=""):
    jobs = minidom.parse(jobsfile)
    par = minidom.parse(parfile)
    solver = jobs.getElementsByTagName("solver")[0]
    parsets = par.getElementsByTagName(tagPrefix + "set")
    system["solver"] = [
        x for x in parsets if solver.attributes["parId"].value == x.attributes["id"].value
    ][0]


def get_refs(generators, parsets, iidmfile):
    if not os.path.isfile(iidmfile):
        return 0
    iidm = minidom.parse(iidmfile)
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
                vlevel = gen.parentNode.attributes["nominalV"]
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
    # logs = file.createElement(tagPrefix+'logs')
    # app1 = file.createElement(tagPrefix+'appender')
    # app1.setAttribute('tag', '')


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
        <solver lib="dynawo_SolverIDA" parFile="{{system['name']}}.par" parId="{{system['solver'].attributes['id'].value}}"/>
        <modeler compileDir="outputs/compilation">
            <!-- <network iidmFile="{{system['name']}}.iidm" parFile="{{system['name']}}.par" parId="Network"/> -->
            <dynModels dydFile="{{system['name']}}.dyd"/>
            <precompiledModels useStandardModels="true"/>
            <modelicaModels useStandardModels="true"/>
        </modeler>
        <simulation startTime="{{system['simulation']['startTime']}}" stopTime="{{system['simulation']['stopTime']}}"/>
        <outputs directory="outputs">
            <curves inputFile="{{system['name']}}.crv" exportMode="CSV"/>

            <logs><appender tag="" file="dynawo.log" lvlFilter="DEBUG"/><appender tag="VARIABLES" file="dynawoVariables.log" lvlFilter="DEBUG"/></logs></outputs>
    </job>
</jobs>
    """
    template = jinja2.Template(template_src)
    with open(output, "w") as f:
        f.write(template.render(system=system))


def gen_dyd(system, output):
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
<dyn:dynamicModelsArchitecture xmlns:dyn="http://www.rte-france.com/dynawo">
    {% for model in models %}
    <dyn:blackBoxModel id="{{model.attributes['id'].value}}" lib="{{model.attributes['lib'].value}}" parFile="{{system['name']}}.par" parId="{{model.attributes['parId'].value}}" />
    <dyn:blackBoxModel id="IBus_{{model.attributes['id'].value}}" lib="InfiniteBusFromTable" parFile="{{system['name']}}.par" parId="IBus_{{model.attributes['id'].value}}"/>
    <dyn:connect id1="{{model.attributes['id'].value}}" var1="generator_terminal" id2="IBus_{{model.attributes['id'].value}}" var2="infiniteBus_terminal"/>
    <dyn:connect id1="{{model.attributes['id'].value}}" var1="generator_omegaRefPu_value" id2="IBus_{{model.attributes['id'].value}}" var2="infiniteBus_omegaRefPu"/>
    {% endfor %}
</dyn:dynamicModelsArchitecture>
    """
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
    <par name="infiniteBus_TableFile" type="STRING" value="table.txt"/>
  </set>
  {% endfor -%}

   <set id="IDAOrder2">
    <par type="INT" name="order" value="2"/>
    <par type="DOUBLE" name="initStep" value="1e-9"/>
    <par type="DOUBLE" name="minStep" value="1e-9"/>
    <par type="DOUBLE" name="maxStep" value="1"/>
    <par type="DOUBLE" name="absAccuracy" value="1e-6"/>
    <par type="DOUBLE" name="relAccuracy" value="1e-6"/>
    <par type="DOUBLE" name="minimalAcceptableStep" value="1e-10"/>
    <par type="INT" name="maximumNumberSlowStepIncrease" value="40"/>
  </set>
</parametersSet>
    """
    template = jinja2.Template(template_src)
    with open(output, "w") as f:
        f.write(template.render(system=system, parlist=parlist))


# {{ system['solver'].toxml() }}
# {% for param in modelpars.getElementsByTagName('reference') -%}
# <par name="{{param.attributes['name'].value}}" type="{{param.attributes['type'].value}}" value="1"/>
# {% endfor -%}


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


def gen_replay_files(root_dir, model, terminals_csv, output_dir="replay/"):
    os.makedirs(output_dir, exist_ok=True)
    gen_table(terminals_csv, output_dir)
    # gen_table(csvfile, output_dir)
    in_jobs, in_par, in_dyd, in_iidm, in_crv = [
        root_dir + model + x for x in [".jobs", ".par", ".dyd", ".iidm", ".crv"]
    ]
    out_jobs, out_par, out_dyd, out_crv = [
        output_dir + model + x for x in [".jobs", ".par", ".dyd", ".crv"]
    ]
    # remove_namespaces(in_dyd, 'dyn')
    # remove_namespaces(in_iidm, 'iidm')
    system = get_jobs_config(in_jobs)
    gen_dict = get_generators(in_dyd, "dyn:")
    get_gen_params(in_par, gen_dict)
    # solver_params = gen_dict['solver']
    # gen_dict.pop('solver')
    parlist = [x["par"] for x in gen_dict.values()]
    get_refs(gen_dict, parlist, root_dir + model + ".iidm")
    system["generators"] = gen_dict
    system["name"] = model
    get_solver_params(in_jobs, in_par, system)
    gen_jobs(system, out_jobs)
    gen_dyd(system, out_dyd)
    gen_par(system, out_par)
    os.system("cp {}*_replay.crv {}/{}.crv".format(root_dir, output_dir, model))
    return system
