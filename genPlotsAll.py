#imports
import os, sys, glob

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from blimpy import Waterfall
from turbo_seti.find_event.plot_event import plot_waterfall
from blimpy.io.hdf_reader import H5Reader

def band(file, tol=0.7):

    L = [1.10, 1.90]
    S = [1.80, 2.80]
    C = [4.00, 7.80]
    X = [7.80, 11.20]

    h5 = H5Reader(file, load_data=False)
    hdr = h5.read_header()

    dirMaxf = hdr['fch1'] * 10**-3
    dirMinf = maxf - np.abs(hdr['foff']*hdr['nchans'])*10**-3

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

def plotWfSep(satCsv, h5Path, memLim=20):

    # get target name and sat name
    satName, targetName = decryptSepName(satCsv)

    # plot waterfall
    wf = Waterfall(h5Path, max_load=memLim)

    b = band(h5Path)
    if type(b) == str:
        raise Exception("No band found for this file")

    plt.figure(figsize=(19.5, 15))
    wf.plot_all(f_start=b*10**3, f_stop=b*10**3)
    plt.savefig(f"{targetName}_{satName.replace(' ','_')}_wf.png", bbox_inches='tight', transparent=False)

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
    fig.savefig(f"{targetName}_{satName.replace(' ', '_')}_separation.png", bbox_inches='tight', transparent=False)

def main():

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--h5Dir', help='Directory with h5 files to run on', default=None)
    parser.add_argument('--csvDir', help='Directory with separation csvs to run on', default=os.getcwd())
    parser.add_argument('--memLim', help='Memory limit for reading in the h5 files', default=20)
    args = parser.parse_args()

    if args.csvDir[-1] != '/':
	    args.csvDir += '/'

    csvs = glob.glob(args.csvDir+'*separation*0000*.csv')

    if not args.h5Dir:
        affectedFiles = pd.read_csv('files_affected_by_sats.csv')
        h5Files = np.array(affectedFiles['filepath'])
        h5Files = h5Files[affectedFiles['satellite?'] == True]
    else:
        if args.h5Dir[-1] != '/':
            args.h5Dir += '/'

        h5Files = glob.glob(args.h5Dir + '*.h5')
    print(csvs)
    print(h5Files)

    for csv, h5 in zip(csvs, h5Files):
        print(f'Plotting for {h5}')
        plotWfSep(csv, h5, memLim=args.memLim)

if __name__ == '__main__':
    sys.exit(main())
