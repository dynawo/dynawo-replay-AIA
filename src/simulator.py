import os, shutil, jinja2
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt
from xml.dom import minidom
from allcurves import *
from replay import *
import logging, datetime
from pathlib import Path


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
    add_logs(jobspath)
    change_curve_file(jobspath, crvfile)
    cd = ''
    if cd_dir:
        cd = 'cd '+dir+' && '
    logging.info('simulation start')
    os.system(cd+'dynawo-RTE_master_2022-11-03 jobs '+jobspath)
    logging.info('simulation end')
    if outdir:
        os.makedirs(outdir, exist_ok=True)
        os.system('cp -rf {}/outputs {}/'.format(dir,outdir))
        # os.system('cp -rf '+dir+'/{*.jobs, *.crv, *.iidm, *.par, *.dyd, *.txt} ' + outdir + '/'.format(dir,outdir))
        os.system('cp -rf {}/{}.dyd {}/'.format(dir,name,outdir))
        for ext in ['.jobs', '.crv', '.par', '.txt']:
            os.system('cp -rf {}/*{} {}/'.format(dir,ext,outdir))
        #copy .dyd of the generator. Its full path must be in the main .jobs file
        file = minidom.parse(jobspath)
        models = file.getElementsByTagName('dynModels')[0]
        dydfile = models.getAttribute('dydFile')
        dydfilename = subprocess.getoutput('basename '+dydfile).split('.')[0]
        if os.path.isfile(dydfile):
            os.system('mv {} {}/'.format(dydfile,outdir))
            change_jobs_file(outdir+'/'+name+'.jobs', dydfilename+'.dyd')
            change_curve_file(outdir+'/'+name+'.jobs', name+'.crv')

def replay(jobspath, crvfile, terminals_csv, outdir, single_gen = True):
    name = subprocess.getoutput('basename '+jobspath).split('.')[0]
    dir = subprocess.getoutput('dirname '+jobspath)+'/'
    os.makedirs(outdir+'/outputs', exist_ok=True)
    gen_replay_files(dir, name, terminals_csv, outdir)
    outdir = os.path.abspath(outdir)+'/'
    if single_gen:
        replay_single_generators(name, outdir)
    else:
        run_simulation(outdir+name+'.jobs', crvfile, '', cd_dir = True)

def replay_single_generators(name, outdir):
    dydfile = outdir+name+'.dyd'
    crvfile_name = name+'.crv'
    crvfile = outdir+crvfile_name
    file = minidom.parse(dydfile)
    generators = get_generators(dydfile)
    gen_ids = []
    for gen in generators:
        system = {}
        system['generators'] = {gen : generators[gen]}
        system['name'] = name
        gen_id = generators[gen]['dyd'].attributes['id'].value
        gen_ids.append(gen_id)
        gen_dydfile = outdir+'/'+gen_id +'.dyd'
        gen_jobsfile = outdir+name+'.jobs'
        gen_dyd(system, gen_dydfile)
        change_jobs_file(gen_jobsfile, gen_dydfile)
        run_simulation(gen_jobsfile, crvfile_name, outdir+gen_id, cd_dir = True)
        logging.info("Replay generator " + gen_id)
    change_jobs_file(gen_jobsfile, name+'.dyd')
    with open(outdir+'generators.txt', 'w') as f:
        f.write('\n'.join(gen_ids))

def plot_csv(csvfile, outputfile, title="Simulation", num_curves=5):
    df = pd.read_csv(csvfile, sep=';')
    t = df.iloc[:,0]
    df = df.iloc[:,1:-1]
    N = df.shape[1]
    if num_curves:
        N = num_curves
    plt.plot(t, df.iloc[:,0:N])
    plt.legend(df.columns[0:N])
    plt.xlabel('Time (s)')
    plt.title(title)
    plt.savefig(outputfile, dpi=300)
    plt.close('all')

def original_vs_replay(original_csv, replay_csv, outputdir, title="Simulation"):
    df = pd.read_csv(original_csv, sep=';')
    t = df.iloc[:,0]
    df = df.iloc[:,1:-1]
    df2 = pd.read_csv(replay_csv, sep=';')
    t2 = df2.iloc[:,0]
    df2 = df2.iloc[:,1:-1]
    with open(outputdir+'vars.txt', 'a') as f:
        f.write(replay_csv+'\t')
        f.write('Original: {}, replay: {} \n'.format(df.shape, df2.shape))
    for c in df2.columns:
        plt.plot(t, df[c], label='original')
        plt.plot(t2, df2[c], label='replay', linestyle='--')
        plt.xlabel('Time (s)')
        plt.title(title+ ' '+c)
        plt.legend()
        plt.savefig(outputdir+'/'+c+'.png', dpi=300)
        plt.close('all')

def original_vs_replay_generators(original_csv, replay_dir):
    """ Plot original and replayed curves for each generator in replay_dir """
    with open(replay_dir+'generators.txt') as file:
        generators = [line.rstrip() for line in file]
    for gen in generators:
        gen_dir = "{}/{}/".format(replay_dir, gen)
        fig_dir = replay_dir+'/fig/'+gen+'/'
        os.makedirs(fig_dir, exist_ok=True)
        with open(fig_dir+'vars.txt', 'w') as f:
            f.write(gen+'\n')
        original_vs_replay(original_csv, gen_dir+'/outputs/curves/curves.csv', fig_dir, title="")
        
    

def runner(jobsfile, output_dir = "replay/", run_original = True, gen_crv = True, gen_csv = True, single_gen = True):
    error = {}
    compression = {}
    name = subprocess.getoutput('basename '+jobsfile).split('.')[0]
    dir = subprocess.getoutput('dirname '+jobsfile)+'/'
    replay_outdir = output_dir+name+'/'
    simulation_outdir = 'simulations/{}/'.format(name)
    os.makedirs(replay_outdir, exist_ok = True)
    os.makedirs(simulation_outdir, exist_ok = True)
    logging.basicConfig(
        filename='simulations/{}/simulation.log'.format(name),
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S')
    crvfile = dir+name+'.crv'
    os.system( 'cp '+crvfile + ' ' + dir+name+'_orig.crv')
    replay_crv = dir+name+'_replay.crv'
    start = datetime.datetime.now()
    logging.info("\nExecution of " + jobsfile + " started at " + str(start))
    if not os.path.isfile(replay_crv):
        shutil.copyfile(crvfile, replay_crv)
    # begin pipeline execution
    print("\n***\n"+jobsfile+"\n***\n")
    if run_original:
        print("\nRunning original")
        run_simulation(jobsfile, name+"_replay.crv", simulation_outdir+'/original/')
        logging.info("Original simulation done")
    if gen_crv:
        print("\nGenerating curves")
        gen_all_curves(jobsfile, target = 'terminals', newvarlogs = True)
        logging.info('generated .crv for all terminals')
    if gen_csv:
        print("\nGenerating CSV with terminal curves")
        run_simulation(jobsfile, name+"_terminals.crv", simulation_outdir+'/terminals/')
        logging.info("Generated CSV with terminal curves")
    print("\nReplaying")
    terminals_csv = simulation_outdir+'/terminals/outputs/curves/curves.csv'
    original_csv = simulation_outdir+'/original/outputs/curves/curves.csv'
    replay_csv = simulation_outdir+'/replay/outputs/curves/curves.csv'


    print("Plotting results")
    logging.info("Plotting results")
    if single_gen:
        replay(jobsfile, name+".crv", terminals_csv, simulation_outdir+'/replay/', single_gen = True)
        logging.info("Finished replay")
        original_vs_replay_generators(original_csv, simulation_outdir+'/replay/')
    else:
        replay(jobsfile, name+".crv", terminals_csv, simulation_outdir+'/replay/', single_gen = False)
        logging.info("Finished replay")
        plot_csv(original_csv, simulation_outdir+'{}_original.png'.format(name), title=name+' Original')
        plot_csv(replay_csv, simulation_outdir+'{}_replay.png'.format(name), title=name+' Replay')
        original_vs_replay(original_csv, replay_csv, simulation_outdir, title=name+' Original vs Replay')
    return error, compression

root_dir='examples_copy/DynaSwing'
# root_dir='../data/examples/DynaSwing/WSCC9/WSCC9_Fault/WSCC9.jobs'
root_dir='../data/IEEE57/IEEE57_Fault/IEEE57.jobs'
# root_dir='../data/smallcase/IEEE57.jobs'
# root_dir='../data/FicheI3SM/FicheI3SM.jobs'
# root_dir='../data/Kundur_Example13/KundurExample13.jobs'
root_dir='../data/examples/DynaSwing/IEEE14/IEEE14_Fault/IEEE14.jobs'
# root_dir='../data/TestCase3/TestCase3.jobs'
# root_dir='examples_copy/DynaSwing/GridForming_GridFollowing/DisconnectLine/'
# root_dir='../data/largecase/tFin/fic.jobs'
output_dir='replay/'
gen_curves = True
gen_csv = True

if __name__ == '__main__':
    runner(root_dir, output_dir, run_original = True, gen_crv = True, gen_csv = True, single_gen = True)
    # runner(root_dir, output_dir, run_original = False, gen_crv = False, gen_csv = False, single_gen = True)
    # runner(root_dir, output_dir, run_original = False, gen_curves = False, gen_csv = False, single_gen = True)
