#imports
import os, sys, glob

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import argparse

from blimpy import Waterfall
from turbo_seti.find_event.plot_event import plot_waterfall

from genPlotsAll import plotWfSep

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--target', help='Name of target file to plot', default=False)
    parser.add_argument('--dir', help='Directory of target file', default=os.getcwd())
    args = parser.parse_args()

    csvs = glob.glob(args.dir+'/*separation*0000*.csv')

    affectedFiles = pd.read_csv(args.dir+'/files_affected_by_sats.csv')
    h5Files = np.array(affectedFiles['filepath'])

    h5Path = None
    csvPath = None
    for h5, csv in zip(h5Files, csvs):
        if h5.find(args.target)!=-1 and h5.find('0000')!=-1:
            h5Path = h5
            csvPath = csv
            break

    try:
        plotWfSep(csv, h5)
    except Exception as e:
        print(e)
        print()
        raise ValueError('Target name was either mistyped or was not affected by satellites')

if __name__ == '__main__':
    sys.exit(main())
