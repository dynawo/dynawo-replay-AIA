import os, shutil, jinja2
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt
from xml.dom import minidom
from allcurves import *
from replay import *
import logging, datetime

logging.basicConfig(
    filename='simulations/simulation.log',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')

def compress_reconstruct(root, ranks = [10], gen_curves = True, gen_csv = True, target = "states"):
    error = {}
    compression = {}
    for jobsfile in glob.iglob(root_dir + '**/*.jobs', recursive=True):
        print(jobsfile)
        name = subprocess.getoutput('basename '+jobsfile).split('.')[0]
        dir = subprocess.getoutput('dirname '+jobsfile)
        start = datetime.datetime.now()
        logging.info("\nExecution of " + jobsfile + " started at " + str(start))
        # begin pipeline execution
        print("\n***\n"+jobsfile+"\n***\n")
        if gen_curves:
            gen_all_curves(jobsfile, target = target, newvarlogs = True)
        if gen_csv:
            os.system('dynawo-RTE_master_2022-11-03 jobs '+jobsfile)
            os.system('mv {}/outputs/curves/curves.csv {}/outputs/curves/{}_curves.csv'.format(dir,dir,target))
            logging.info('finished Dynawo simulation')
        csvfile = dir+'/outputs/curves/{}_curves.csv'.format(target)
        if not os.path.isfile(csvfile):
            logging.error(csvfile + " does not exist")
            continue
        df = pd.read_csv(csvfile, sep=';')
        dfsize = os.path.getsize(csvfile)
        logging.info("read CSV")

        print("{} loaded".format(jobsfile))
        compress_and_save(df, name, target, ranks=ranks)
        logging.info("compressed matrix")
        reconstructed = reconstruct_from_disk(name, target, ranks=ranks)
        logging.info("reconstructed matrix")
        error[name], compression[name] = plot_results(df, dfsize, name, target, ranks=ranks)
        logging.info("plot results")
        # log finish
        end = datetime.datetime.now()
        elapsed = end-start
        logging.info("Execution of " + jobsfile + " finished at " + str(end) + ". Time elapsed: " + str(elapsed)+"\n")
        logging.info("\n")
        return error, compression

import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt

def plot_csv(csvfile, outputfile, title="Simulation"):
    df = pd.read_csv(csvfile, sep=';')
    t = df.iloc[:,0]
    df = df.iloc[:,1:-1]
    plt.plot(t, df)
    plt.xlabel('Time (s)')
    plt.title(title)
    plt.savefig(outputfile, dpi=300)
    plt.close('all')

def run_simulation(jobspath, crvfile, outdir):
    name = subprocess.getoutput('basename '+jobspath).split('.')[0]
    dir = subprocess.getoutput('dirname '+jobspath)+'/'
    change_curve_file(jobspath, crvfile)
    add_logs(jobspath)
    os.system('dynawo-RTE_master_2022-11-03 jobs '+jobspath)
    # plot_csv('{}/outputs/curves/curves.csv'.format(dir), simulation_outdir+'{}_orig.png'.format(name), title=name+' Original')
    os.system('mv {}/outputs/* {}'.format(dir,outdir))
    logging.info('ran simulation')

def replay(root, output_dir = "replay/", run_original = True, gen_curves = True, gen_csv = True):
    error = {}
    compression = {}
    print(root)
    for jobsfile in glob.iglob(root_dir + '**/*.jobs', recursive=True):
        print(jobsfile)
        start = datetime.datetime.now()
        logging.info("\nExecution of " + jobsfile + " started at " + str(start))
        name = subprocess.getoutput('basename '+jobsfile).split('.')[0]
        dir = subprocess.getoutput('dirname '+jobsfile)+'/'
        replay_outdir = output_dir+name+'/'
        simulation_outdir = 'simulations/{}/'.format(name)
        os.makedirs(replay_outdir, exist_ok = True)
        os.makedirs(simulation_outdir, exist_ok = True)
        crvfile = dir+name+'.crv'
        os.system( 'cp '+crvfile + ' ' + dir+name+'_orig.crv')
        replay_crv = dir+name+'_replay.crv'
        if not os.path.isfile(replay_crv):
            shutil.copyfile(crvfile, replay_crv)
        # begin pipeline execution
        print("\n***\n"+jobsfile+"\n***\n")
        if run_original:
            run_simulation(jobsfile, name+".crv", simulation_outdir)
        if gen_curves:
            print("Generating curves")
            gen_all_curves(jobsfile, target = 'terminals', newvarlogs = True)
            logging.info('generated .crv for all terminals')
        if gen_csv:
            print("Generating CSV with terminal curves")
            change_curve_file(jobsfile, '{}_terminals.crv'.format(name))
            os.system('dynawo-RTE_master_2022-11-03 jobs '+jobsfile)
            os.system('mv {}/outputs/curves/curves.csv {}/outputs/curves/terminals_curves.csv'.format(dir,dir))
            change_curve_file(jobsfile, '{}.crv'.format(name))
            logging.info('finished Dynawo simulation')
        csvfile = dir+'/outputs/curves/terminals_curves.csv'
        print(csvfile)
        if not os.path.isfile(csvfile):
            logging.error(csvfile + " does not exist")
            print(csvfile + " does not exist")
            continue
        print('Replaying')
        system = gen_replay_files(dir, name, replay_outdir)
        os.system('cp {}/{}_replay.crv {}/{}.crv'.format(dir,name, replay_outdir,name))
        replay_jobs = replay_outdir+name+'.jobs'
        os.system('cd {} && dynawo-RTE_master_2022-11-03 jobs {}'.format(replay_outdir, name+'.jobs'))
        csvfile = replay_outdir+'/outputs/curves/curves.csv'
        plot_csv(csvfile, simulation_outdir+'{}_replay.png'.format(name), title=name+' Replay')
        end = datetime.datetime.now()
        elapsed = end-start
        logging.info("Execution of " + jobsfile + " finished at " + str(end) + ". Time elapsed: " + str(elapsed)+"\n")
        logging.info("\n")
        return error, compression

root_dir='examples_copy/DynaSwing'
root_dir='../data/examples/DynaSwing/WSCC9/WSCC9_Fault/'
# root_dir='examples_copy/DynaSwing/IEEE57/IEEE57_Fault/'
# root_dir='examples_copy/DynaSwing/IEEE14/IEEE14_Fault/'
# root_dir='examples_copy/DynaSwing/GridForming_GridFollowing/DisconnectLine/'
# root_dir='largecase/tFin/'
output_dir='replay/'
gen_curves = True
gen_csv = True

replay(root_dir, output_dir, run_original = True, gen_curves = True, gen_csv = True)
# replay(root_dir, output_dir, run_original = False, gen_curves = False, gen_csv = False)
