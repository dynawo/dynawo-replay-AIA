import os, shutil
import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt
import glob
import subprocess
import logging, datetime
from xml.dom import minidom
from sklearn.utils.extmath import randomized_svd

# logging.basicConfig(
#     filename='execution.log', 
#     format='%(asctime)s %(levelname)-8s %(message)s',
#     level=logging.INFO,
#     datefmt='%Y-%m-%d %H:%M:%S')

def add_logs(jobsfilename, tagPrefix = ''):
    file = minidom.parse(jobsfilename)
    logs = file.getElementsByTagName(tagPrefix+'logs')   
    if logs: 
        logs[0].parentNode.removeChild(logs[0])
    outputs = file.getElementsByTagName(tagPrefix+'outputs')[0]
    logs = file.createElement(tagPrefix+'logs')
    app1 = file.createElement(tagPrefix+'appender')
    app1.setAttribute('tag', '')
    app1.setAttribute('file', 'dynawo.log')
    app1.setAttribute('lvlFilter', 'DEBUG')
    app2 = file.createElement(tagPrefix+'appender')
    app2.setAttribute('tag', 'VARIABLES')
    app2.setAttribute('file', 'dynawoVariables.log')
    app2.setAttribute('lvlFilter', 'DEBUG')
    logs.appendChild(app1)
    logs.appendChild(app2)
    outputs.appendChild(logs)
    with open(jobsfilename, 'w') as out:
        # out.write(file.toprettyxml())
        file.writexml(out)
        out.close()


def compress_and_save(df, name, target = 'states', outpath = 'results', ranks=[10], randomized = True):
    df = np.array(df.iloc[:,1:-1]).T
    error = []
    compression = []
    os.makedirs(outpath+'/'+name, exist_ok = True)
    for r in ranks:
        np.random.RandomState(1)
        f, (ax1, ax2) = plt.subplots(2,1)
        f.tight_layout(pad=2)
        idx = np.random.permutation(np.arange(df.shape[0]))[0:60]
        ax1.plot(df[idx,:].T)
        ax1.set_title(name)
        # plt.savefig("plots/curves_{}.png".format(filename))
        if randomized:
            u,d,v = randomized_svd(df, r)
        else:
            u,d,v = np.linalg.svd(np.matrix(g(d[0:r]), v[0:r,:]))
        with open(outpath+'/{}/{}_{}_compressed_rank_{}.npy'.format(name, name, target, r), "wb") as f:
            np.save(f, u)
            np.save(f, d)
            np.save(f, v)

def reconstruct_from_disk(name, target = 'states', path = 'results', ranks=[10]):
    reconstructed = []
    for r in ranks:
        filepath = '{}/{}/{}_{}_compressed_rank_{}.npy'.format(path,name,name,target,r)
        with open(filepath, 'rb') as f:
            u = np.load(f)
            d = np.load(f)
            v = np.load(f)
            fsize = os.path.getsize(filepath)
        reconstructed.append([np.dot(u, np.dot(np.diag(d), v)), [u,d,v], fsize])
    return reconstructed

def plot_results(df, dfsize, name, target='states', path='results', ranks=[10]):
    df = np.array(df.iloc[:,1:-1]).T
    error = []
    compression = []
    os.makedirs("{}/{}".format(path,name), exist_ok = True)
    reconstructed = reconstruct_from_disk(name, target=target, ranks=ranks)
    for M_r, udv, fsize in reconstructed:
        u,d,v = udv
        r = d.size
        e = np.linalg.norm(df-M_r, ord='fro')
        c = fsize/dfsize
        compression.append(c)
        error.append(e)
        f, (ax1, ax2) = plt.subplots(2,1)
        f.tight_layout(pad=2)
        np.random.RandomState(0)
        idx = np.random.permutation(np.arange(df.shape[0]))[0:60]
        ax1.plot(df[idx,:].T)
        ax1.set_title(name)
        # plt.savefig("plots/curves_{}.png".format(name))
        ax2.plot(M_r[idx,:].T)
        ax2.set_title("LRA  |  r = {}  |  c = {:0.4f}  |  e = {:0.4f}".format(r,c,e))
        plt.savefig("{}/{}/{}_{}_curves_rank_{}.png".format(path,name, name, target, r), dpi=300, bbox_inches='tight')
        plt.close('all')
        ##########
        f, (ax1, ax2) = plt.subplots(2,1)
        f.tight_layout(pad=3)
        ax1.plot(u[:,0:r])
        ax1.set_title("Top {} left SV".format(r))
        ax2.plot(v[0:r,:].T)
        ax2.set_title("Top {} right SV".format(r))
        plt.savefig("{}/{}/{}_{}_rank_{}.png".format(path, name, name, target, r), dpi=300, bbox_inches='tight')
        plt.close('all')
        plt.figure()
        plt.plot(d)
        plt.title(name)
        plt.savefig("{}/{}/{}_{}_eigvals_{}.png".format(path, name, name, target, r), dpi=300, bbox_inches='tight')
        plt.close('all')
    return error, compression

def plot_svd(df, filename, ranks=[10], randomized = True):
    df = np.array(df.iloc[:,1:-1]).T
    error = []
    compression = []
    os.makedirs("plots/"+filename, exist_ok = True)
    for r in ranks:
        np.random.RandomState(1)
        f, (ax1, ax2) = plt.subplots(2,1)
        f.tight_layout(pad=2)
        idx = np.random.permutation(np.arange(df.shape[0]))[0:60]
        ax1.plot(df[idx,:].T)
        ax1.set_title(filename)
        # plt.savefig("plots/curves_{}.png".format(filename))
        if randomized:
            u,d,v = randomized_svd(df, r)
        else:
            u,d,v = np.linalg.svd(np.matrix(g(d[0:r]), v[0:r,:]))
        with open('results/{}/{}_compressed_rank_{}.npy'.format(filename, filename, r)) as f:
            np.save(f, u)
            np.save(f, d)
            np.save(f, v)
        M_r = np.dot(u[:,0:r], np.dot(np.diag(d[0:r]), v[0:r,:]))
        N, M = df.shape
        M_r_size = N*r+r+M*r
        c = M_r_size/(N*M)
        compression.append(c)
        e = np.linalg.norm(df-M_r, ord='fro')
        error.append(e)
        ax2.plot(M_r[idx,:].T)
        ax2.set_title("LRA  |  r = {}  |  c = {:0.4f}  |  e = {:0.4f}".format(r,c,e))
        plt.savefig("results/{}/{}_curves_rank_{}.png".format(filename, filename, r), dpi=300, bbox_inches='tight')
        plt.close('all')
        ##########
        f, (ax1, ax2) = plt.subplots(2,1)
        f.tight_layout(pad=3)
        ax1.plot(u[:,0:r])
        ax1.set_title("Top {} left SV".format(r))
        ax2.plot(v[0:r,:].T)
        ax2.set_title("Top {} right SV".format(r))
        plt.savefig("results/{}/{}_rank_{}.png".format(filename, filename, r), dpi=300, bbox_inches='tight')
        plt.close('all')
        plt.figure()
        plt.plot(d)
        plt.title(filename)
        plt.savefig("results/{}/{}_eigvals_{}.png".format(filename, filename, r), dpi=300, bbox_inches='tight')
        plt.close('all')
    return error, compression
    # M = np.array(df.iloc[:,1:-1])
    # Cxx = np.cov(M.T)
    # plt.imshow(Cxx)
    # plt.colorbar()
    # plt.savefig("plots/C_{}.png".format(filename))

def change_curve_file(jobsfile, curvefilename, tag_prefix = ''):
    file = minidom.parse(jobsfile)
    curves = file.getElementsByTagName(tag_prefix+'curves')[0]
    curves.setAttribute('inputFile', curvefilename)
    with open(jobsfile, 'w') as out:
        # out.write(file.toprettyxml())
        file.writexml(out)
        out.close()

def change_jobs_file(jobsfile, dydfilename, tag_prefix = ''):
    file = minidom.parse(jobsfile)
    models = file.getElementsByTagName(tag_prefix+'dynModels')[0]
    models.setAttribute('dydFile', dydfilename)
    with open(jobsfile, 'w') as out:
        # out.write(file.toprettyxml())
        file.writexml(out)
        out.close()


def gen_all_curves(jobsfile, target = "states", newvarlogs = False, recursive=True):
    name = subprocess.getoutput('basename '+jobsfile).split('.')[0]
    dir = subprocess.getoutput('dirname '+jobsfile)
    # os.system("""egrep -rl '<dyn:' {}/ | xargs -I sed -i '' 's/<dyn:/</g'  """.format(dir))
    os.system("""sed -i 's/<dyn:/</g' {} """.format(jobsfile))
    os.system("""sed -i 's/<\/dyn:/<\//g' {} """.format(jobsfile))
    os.system("""sed -i 's/:dyn//g' {} """.format(jobsfile))
    logfile = dir+'/outputs/logs/dynawoVariables.log'
    states = subprocess.getoutput("""sed -n '/X variables$/,/alias/p' {} | sed 's/.* DEBUG | [0-9]\+ \\(.*\\)/\\1/p' >> {}/states.txt """.format(logfile, dir))
    terminals = subprocess.getoutput(""" sed -n '/X variables$/,/alias/p' {} | sed '/terminal/!d' | sed 's/.* DEBUG | [0-9]\+ \\(.*\\)/\\1/p' >>  {}/terminals.txt """.format(logfile, dir))
    dydfile = dir + '/{}.dyd'.format(name)
    models = subprocess.getoutput("""sed -n 's/.*id="\\([^"]*\\).*/\\1/p' {} > {}/models.txt """.format(dydfile, dir))
    os.system('sh genallcrv.sh {}/models.txt {}/{}.txt'.format(dir, dir, target))
    os.system('mv allcurves.crv {}/{}_terminals.crv'.format(dir, name))
    logging.info('generated allcurves_{}.crv'.format(target))


# root_dir='/home/gimenezp/dynawo-curve-reconstruction/scripts/testcaseaia/'
# root_dir='/home/gimenezp/dynawo-curve-reconstruction/scripts/IEEE14_Fault/'
# # root_dir='/home/gimenezp/dynawo-curve-reconstruction/scripts/examples/DynaSwing/'
# # root_dir='/home/gimenezp/dynawo-curve-reconstruction/scripts/largecase/tFin/'
# target = 'terminals'
# gen_curves = True
# gen_csv = True
# ranks=[2,5,10,30]
# error, compression = compress_reconstruct(root_dir, ranks = ranks, gen_curves = gen_curves, gen_csv = gen_csv, target = target)

# error_df = pd.DataFrame.from_dict(error, orient='index')
# error_df.columns = ranks
# print(error_df)
# compression_df = pd.DataFrame.from_dict(compression, orient='index')
# compression_df.columns = ranks
# print(compression_df)
# df[['index','column']] = df.index.values.tolist()
# df = df.set_index(['index','column'])[0].unstack().rename_axis(None).rename_axis(None, axis=1)
