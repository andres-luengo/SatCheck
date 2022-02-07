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

    plot_f, plot_data = wf.grab_data()

    extent=(plot_f[-1], plot_f[0], 0.0, (wf.timestamps[-1]-wf.timestamps[0])*24.*60.*60)

    fig, ax = plt.subplots(figsize=(8,10))

    this_plot = plot_waterfall(wf, targetName)

    data = np.flipud(np.fliplr(np.array(this_plot.get_array())))

    this_plot2 = plt.imshow(data,
            aspect='auto',
            rasterized=True,
            interpolation='nearest',
            extent=extent)

    cax = fig.add_axes([0.94, 0.11, 0.03, 0.77])
    fig.colorbar(this_plot2,cax=cax,label='Normalized Power (Arbitrary Units)')

    fig.savefig(f"{targetName}_{satName.replace(' ','_')}_wf.png", bbox_inches='tight', transparent=False)

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
    parser.add_argument('--dir', help='Directory with h5 files to run on', default=None)
    args = parser.parse_args()

    csvs = glob.glob(os.getcwd()+'/*separation*0000*.csv')

    if not args.dir:
        affectedFiles = pd.read_csv('files_affected_by_sats.csv')
        h5Files = np.array(affectedFiles.columns.values.tolist()[1:])
    else:
        if args.dir[-1] != '/':
            args.dir += '/'

        h5Files = glob.glob(args.dir + '*')

    goodFiles = []
    for h5 in h5Files:
         if h5.split('.')[-2] == '0000':
            goodFiles.append(h5)

    for csv, h5 in zip(csvs, goodFiles):
        plotWfSep(csv, h5)

if __name__ == '__main__':
    sys.exit(main())
