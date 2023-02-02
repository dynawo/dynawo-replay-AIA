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


def run_simulation(jobspath, crvfile, outdir, cd_dir = False):
    name = subprocess.getoutput('basename '+jobspath).split('.')[0]
    dir = subprocess.getoutput('dirname '+jobspath)+'/'
    change_curve_file(jobspath, crvfile)
    add_logs(jobspath)
    cd = ''
    if cd_dir:
        cd = 'cd '+dir+' && '
    os.system(cd+'dynawo-RTE_master_2022-11-03 jobs '+jobspath)
    if outdir:
        os.makedirs(outdir, exist_ok=True)
        os.system('cp -rf {}/outputs/* {}/'.format(dir,outdir))
    logging.info('ran simulation')

def replay(jobspath, crvfile, terminals_csv, outdir):
    name = subprocess.getoutput('basename '+jobspath).split('.')[0]
    dir = subprocess.getoutput('dirname '+jobspath)+'/'
    os.makedirs(outdir+'/outputs', exist_ok=True)
    gen_replay_files(dir, name, terminals_csv, outdir)
    print(outdir+name+'.jobs')
    outdir = os.path.abspath(outdir)+'/'
    run_simulation(outdir+name+'.jobs', crvfile, '', cd_dir = True)

# def original_vs_table(original_csv, table):

def plot_csv(csvfile, outputfile, title="Simulation", num_curves=5):
    df = pd.read_csv(csvfile, sep=';')
    t = df.iloc[:,0]
    df = df.iloc[:,1:-1]
    N = df.shape[1]
    if num_curves:
        N = num_curves
    # df = df.iloc[:,0:N]
    # plt.plot(t, df)
    # df.plot()
    plt.plot(t, df.iloc[:,0:N])
    plt.legend(df.columns[0:N])
    plt.xlabel('Time (s)')
    # plt.xlabel('Sample')
    plt.title(title)
    plt.savefig(outputfile, dpi=300)
    plt.close('all')

def original_vs_replay(original_csv, replay_csv, outputfile, title="Simulation"):
    df = pd.read_csv(original_csv, sep=';')
    t = df.iloc[:,0]
    df = df.iloc[:,1:-1]
    df2 = pd.read_csv(replay_csv, sep=';')
    t2 = df2.iloc[:,0]
    df2 = df2.iloc[:,1:-1]
    print(df.shape, df2.shape)
    for i,c in enumerate(df.columns):
        plt.plot(t, df.iloc[:,i], label='original')
        plt.plot(t2, df2.iloc[:,i], label='replay', linestyle='--')
        plt.xlabel('Time (s)')
        plt.title(title+ ' '+c)
        # plt.legend()
        plt.savefig(outputfile+'/'+c+'.png', dpi=300)
        plt.close('all')

def runner(jobsfile, output_dir = "replay/", run_original = True, gen_curves = True, gen_csv = True):
    error = {}
    compression = {}
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
        run_simulation(jobsfile, name+"_replay.crv", simulation_outdir+'/original/')
    if gen_curves:
        print("Generating curves")
        gen_all_curves(jobsfile, target = 'terminals', newvarlogs = True)
        logging.info('generated .crv for all terminals')
    if gen_csv:
        print("Generating CSV with terminal curves")
        run_simulation(jobsfile, name+"_terminals.crv", simulation_outdir+'/terminals/')
    print("Replaying")
    terminals_csv = simulation_outdir+'/terminals/curves/curves.csv'
    original_csv = simulation_outdir+'/original/curves/curves.csv'
    replay_csv = simulation_outdir+'/replay/outputs/curves/curves.csv'

    replay(jobsfile, name+".crv", terminals_csv, simulation_outdir+'/replay/')

    plot_csv(original_csv, simulation_outdir+'{}_original.png'.format(name), title=name+' Original')
    plot_csv(replay_csv, simulation_outdir+'{}_replay.png'.format(name), title=name+' Replay')
    original_vs_replay(original_csv, replay_csv, simulation_outdir, title=name+' Original vs Replay')
    return error, compression

root_dir='examples_copy/DynaSwing'
root_dir='../data/examples/DynaSwing/WSCC9/WSCC9_Fault/WSCC9.jobs'
root_dir='../data/IEEE57/IEEE57_Fault/IEEE57.jobs'
# root_dir='../data/smallcase/IEEE57.jobs'
# root_dir='../data/FicheI3SM/FicheI3SM.jobs'
# root_dir='../data/Kundur_Example13/KundurExample13.jobs'
# root_dir='../data/examples/DynaSwing/IEEE14/IEEE14_Fault/IEEE14.jobs'
# root_dir='examples_copy/DynaSwing/GridForming_GridFollowing/DisconnectLine/'
# root_dir='../data/largecase/tFin/fic.jobs'
output_dir='replay/'
gen_curves = True
gen_csv = True

runner(root_dir, output_dir, run_original = True, gen_curves = True, gen_csv = True)
# runner(root_dir, output_dir, run_original = False, gen_curves = False, gen_csv = False)
