import os, sys
import numpy as np
import pandas as pd
import pickle
import argparse

def findGPSTargs(e):
    file = '/home/ubuntu/scratch/flagged_files_2SD.pkl'

    with open(file, "rb") as f:
        flaggedFiles = pickle.load(f)

    gpsFiles = []
    for ff, freq in zip(flaggedFiles['file name'], flaggedFiles['flagged frequency']):

        # find files with flagged bins in range 1590-1610 MHz
        freq = freq.astype(float)
        whereGPS = np.where((freq > 1600-e)*(freq < 1600+e))[0]

        if len(whereGPS) > 0:
            gpsFiles.append(ff)

    #print(gpsFiles)
    return gpsFiles

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--epsilon', default=10)
    args = parser.parse_args()

    gps = findGPSTargs(float(args.epsilon))

if __name__ == '__main__':
    sys.exit(main())
