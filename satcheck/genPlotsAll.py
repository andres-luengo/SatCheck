#imports
import os, sys, glob, ast

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from blimpy import Waterfall
from turbo_seti.find_event.plot_event import plot_waterfall
from blimpy.io.hdf_reader import H5Reader

import matplotlib as mpl
mpl.rcParams['agg.path.chunksize'] = 10000

def band(file, tol=0.7):

    L = [1.10, 1.90]
    S = [1.80, 2.80]
    C = [4.00, 7.80]
    X = [7.80, 11.20]

    h5 = H5Reader(file, load_data=False)
    hdr = h5.read_header()

    dirMaxf = hdr['fch1'] * 10**-3
    dirMinf = dirMaxf - np.abs(hdr['foff']*hdr['nchans'])*10**-3

    if abs(dirMinf-L[0]) < tol and abs(dirMaxf-L[1]) < tol:
        return L
    elif abs(dirMinf-S[0]) < tol and abs(dirMaxf-S[1]) < tol:
        return S
    elif abs(dirMinf-C[0]) < tol and abs(dirMaxf-C[1]) < tol:
        return C
    elif abs(dirMinf-X[0]) < tol and abs(dirMaxf-X[1]) < tol:
        return X
    else:
        return 'NA'

def decryptSepName(path):

    name = os.path.split(path)[1]

    ii = name.find('separation')

    sat = name[:ii].replace('_', ' ').split('-')
    newSat = sat[0]

    target = name[ii+11:].split('_')[0]

    return newSat, target

def plotH5(satCsv, h5Path, memLim=20, work_dir=None):

    # Set work directory, default to current working directory
    if work_dir is None:
        work_dir = os.getcwd()
    
    # Ensure work_dir exists
    os.makedirs(work_dir, exist_ok=True)

    # get target name and sat names
    sats = []
    for csv in satCsv:
        satName, targetName = decryptSepName(csv)
        sats.append(satName.lstrip('_').rstrip('_'))

    sats = np.unique(np.array(sats))
    satName = ""
    for sat in sats:
        satName += sat + ", "

    satName = satName[:-2]

    # plot waterfall
    wf = Waterfall(h5Path, max_load=memLim)

    b = band(h5Path)
    if type(b) == str:
        raise Exception("No band found for this file")

    plt.figure(figsize=(19.5, 15))
    wf.plot_all(f_start=b[0]*10**3, f_stop=b[1]*10**3)
    plot_path = os.path.join(work_dir, f"{targetName}_{satName.replace(' ','_')}_wf.png")
    plt.savefig(plot_path, bbox_inches='tight', transparent=False)
    plt.close()

def plotSep(satCsv, work_dir=None):

    # Set work directory, default to current working directory
    if work_dir is None:
        work_dir = os.getcwd()
    
    # Ensure work_dir exists
    os.makedirs(work_dir, exist_ok=True)

    # get target name and sat name
    satName, targetName = decryptSepName(satCsv)

    # plot separation
    df = pd.read_csv(satCsv)
    time = df['Time after start']
    sep = df['Separation']

    fig, ax = plt.subplots(figsize=(8,10))
    ax.plot(sep, time, label=satName)
    ax.set_ylabel('Time [s]')
    ax.set_xlabel('Seperation [degrees]')

    minpoint = min(sep)

    minindex = np.where(sep == minpoint)[0] #df['Separation'].index(minpoint)
    mintime = int(time[minindex])

    ax.scatter(minpoint, mintime, s = 50, label = 'Min: ' + str("%.5fdeg" % minpoint) + ', ' + str(mintime) + "s", color='orange')

    ax.legend();
    plot_path = os.path.join(work_dir, f"{targetName}_{satName.replace(' ', '_')}_separation.png")
    fig.savefig(plot_path, bbox_inches='tight', transparent=False)
    plt.close(fig)

def main():

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--h5Dir', help='Directory with h5 files to run on', default=None)
    parser.add_argument('--memLim', help='Memory limit for reading in the h5 files', default=40)
    parser.add_argument('--work_dir', help='directory to store output files, defaults to current working directory', default=None)
    args = parser.parse_args()

    # Set work directory, default to current working directory
    work_dir = args.work_dir if args.work_dir else os.getcwd()
    os.makedirs(work_dir, exist_ok=True)

    affectedFiles = pd.read_csv(os.path.join(work_dir, 'files_affected_by_sats.csv'))

    csvs = np.array([ast.literal_eval(x) for x in affectedFiles['csvPaths']])

    if not args.h5Dir:
        h5Files = np.array(affectedFiles['filepath'])
        h5Files = h5Files[affectedFiles['satellite?'] == True]
    else:
        if args.h5Dir[-1] != '/':
            args.h5Dir += '/'
        h5Files = glob.glob(args.h5Dir + '*.h5')

    for csvList, h5 in zip(csvs, h5Files):
        print(f'Plotting for {h5}')
        plotH5(csvList, h5, memLim=args.memLim, work_dir=work_dir)
        for csv in csvList:
            plotSep(csv, work_dir=work_dir)


if __name__ == '__main__':
    sys.exit(main())
