import os, sys
import numpy as np
import pandas as pd
import pickle
import argparse

def findGPSTargs(e):
    """
    Identify observation files with flagged frequencies in GPS L1 band.
    
    This function searches through a database of flagged observation files to find
    those containing interference in the GPS L1 frequency range (around 1575-1600 MHz).
    This helps identify observations that may be affected by GPS satellite transmissions.
    
    Parameters
    ----------
    e : float
        Epsilon tolerance in MHz around the 1600 MHz center frequency.
        Files with flagged frequencies in the range [1600-e, 1600+e] MHz are returned.
        
    Returns
    -------
    list of str
        List of observation file names that contain flagged frequencies
        in the specified GPS frequency range.
        
    Notes
    -----
    - Reads from hardcoded pickle file: '/home/ubuntu/scratch/flagged_files_2SD.pkl'
    - GPS L1 band is centered around 1575.42 MHz, but uses 1600 MHz as reference
    - Flagged frequencies indicate detected interference or anomalies
    - File path is specific to the original analysis environment
    
    Examples
    --------
    Find GPS-affected files with 10 MHz tolerance:
    
    >>> gps_files = findGPSTargs(10.0)
    >>> print(f"Found {len(gps_files)} files with GPS L1 interference")
    
    Find files with narrow frequency range:
    
    >>> gps_files = findGPSTargs(5.0)  # ±5 MHz around 1600 MHz
    """
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
