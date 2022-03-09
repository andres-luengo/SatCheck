#imports
import os, sys, glob

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from blimpy import Waterfall
from turbo_seti.find_event.plot_event import plot_waterfall

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

    plt.figure(figsize=(19.5, 15))
    wf.plot_all()
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
