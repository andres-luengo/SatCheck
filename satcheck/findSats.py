'''
Modified from Chris Murphy's Satellite code
see: https://github.com/stevecroft/bl-interns/blob/master/chrismurphy/find_satellites.py
'''

import os, sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse

import ephem

from .findSatsHelper import *
from .genPlotsAll import plotSep

def io(n, work_dir=None):
    """
    Get NORAD IDs from UCS database, filtered for satellites likely to have historical data
    """
    # read in the UCS Satellite Database for complete list of satellites
    df = pd.read_csv(queryUCS(work_dir=work_dir))
    
    # Filter out satellites that are unlikely to have historical TLE data
    # Remove rows with missing/invalid NORAD numbers
    df = df.dropna(subset=['NORAD Number'])
    df = df[df['NORAD Number'] > 0]
    
    # If there's a launch date column, filter for satellites launched before 2021
    # This helps reduce queries for very recent satellites when looking for 2020 data
    if 'Date of Launch' in df.columns:
        try:
            df['Launch_Year'] = pd.to_datetime(df['Date of Launch'], errors='coerce').dt.year
            df = df[(df['Launch_Year'].isna()) | (df['Launch_Year'] <= 2021)]
            print(f"Filtered to {len(df)} satellites launched before 2022 (or unknown launch date)")
        except:
            print("Could not filter by launch date, using all satellites")
    
    idList = np.array(df['NORAD Number'].tolist())
    
    # Remove any invalid IDs (NaN, negative, etc.)
    idList = idList[~pd.isna(idList)]
    idList = idList[idList > 0]
    
    print(f"Total satellite IDs to query: {len(idList)}")
    
    return np.array_split(idList, n)

def downloadTLEs(list_of_filenames, n, spacetrack_account=None, spacetrack_password=None, work_dir=None):

    noradIds = io(n, work_dir=work_dir)

    # get relevant TLEs
    allTLEfiles = []
    for idx, nIds in enumerate(noradIds):
        # get comma separated string of relevant ids to get the TLEs
        ids = ','.join(str(i) for i in nIds)  # Remove trailing comma
        tles = query_space_track(list_of_filenames, ids, idx, spacetrack_account=spacetrack_account, spacetrack_password=spacetrack_password, work_dir=work_dir)
        allTLEfiles.append(tles)

    # rewrite all TLEs ase unique files
    baseNames = []
    for lis in allTLEfiles:
        for f in lis:
            baseNames.append(f[:-6])
    baseNames = np.unique(np.array(baseNames))

    sepTLEs = {}
    for name in baseNames:
        for lis in allTLEfiles:
            for f in lis:
                if f[:-6] == name:
                    if name in sepTLEs:
                        sepTLEs[name].append(f)
                    else:
                        sepTLEs[name] = [f]

    # Set work directory, default to current working directory  
    if work_dir is None:
        work_dir = os.getcwd()
    
    # Ensure work_dir exists
    os.makedirs(work_dir, exist_ok=True)

    for key in sepTLEs.keys():
        combined_file_path = os.path.join(work_dir, f"{key}.txt")
        with open(combined_file_path, "wb") as outfile:
            for f in sepTLEs[key]:
                if os.path.exists(f):
                    with open(f, "rb") as infile:
                        outfile.write(infile.read())

                    os.remove(f)

    return np.array([os.path.join(work_dir, name+'.txt') for name in baseNames])

def findSats(dir=None, file=None, pattern='*.h5', plot=False, n=10, /, file_list=None, spacetrack_account=None, spacetrack_password=None, work_dir=None):

    # check that end of args.dir is a /
    if dir != None and not dir[-1] == '/':
        dir += '/'

    # Set work directory, default to current working directory
    if work_dir is None:
        work_dir = os.getcwd()
    
    # Ensure work_dir exists
    os.makedirs(work_dir, exist_ok=True)

    # month conversion
    months = {"01":"jan", "02":"feb","03":"mar","04":"apr","05":"may","06":"jun",
                  "07":"jul","08":"aug","09":"sep","10":"oct","11":"nov", "12":"dec"}

    # read in necessary info from the h5 files
    list_of_filenames = find_files(dir, file, file_list, pattern)
    start_time_mjd, ra_lst, dec_lst = pull_relevant_header_info(list_of_filenames)

    tles = downloadTLEs(list_of_filenames, n, spacetrack_account, spacetrack_password, work_dir=work_dir)

    # Create ephem Observer object for GBT
    gbt = ephem.Observer()
    gbt.long = "-79.839857"
    gbt.lat = "38.432987"
    gbt.elevation = 807.0

    files_affected_by_sats = {}
    for (fil_file, ra, dec, dd) in zip(list_of_filenames, ra_lst, dec_lst, start_time_mjd):

        files_affected_by_sats[fil_file] = [[],[],[]]

        date = convert(dd)
        year = date.split("-")[0]
        mon = date.split("-")[1]
        day1 = date.split("-")[2].split('T')[0]
        filename = months[mon] + '_' + day1 + "_" +year +"_TLEs.txt"

        # figure out which tle to compare to
        whichTLE = np.where(filename == tles)[0]

        # calculate the separation for 5 minutes after the start of observation
        if os.path.exists(filename):
            tle = tles[whichTLE][0]
            satdict = load_tle(tle)
            sat_hit_dict = separation(satdict, ra, dec, date, gbt)
        else:
            print('No satellites to crossmatch, exiting this check')
            break

        if len(sat_hit_dict.keys()) > 0:

            # write information to output files
            for stored_sats_in_obs, unique_sat_info in sat_hit_dict.items():

                outname = os.path.join(work_dir, stored_sats_in_obs.replace(' ','_').replace('(','-').replace(')','-').replace('/', '-')+'_separation_'+fil_file.split('_')[-2] + '_' + fil_file.split('_')[-1]).replace('h5', 'csv')

                if not os.path.exists(outname):

                    print('Writing to: ', outname)
                    separationData = pd.DataFrame(unique_sat_info)
                    separationData.to_csv(outname)

                minpoint = min(unique_sat_info['Separation'])

                minindex = unique_sat_info['Separation'].index(minpoint)
                mintime = unique_sat_info['Time after start'][minindex]

                if plot:
                    plotSep(outname, work_dir=work_dir)
                    #plotSeparation(unique_sat_info, stored_sats_in_obs, fil_file, mintime, minpoint, minindex, work_dir=work_dir)

                files_affected_by_sats[fil_file][0].append(minpoint)
                files_affected_by_sats[fil_file][1].append(mintime)
                files_affected_by_sats[fil_file][2].append(outname)

    # Write csv file of files affected and their minimum separation and time

    # unpack files_affected_by_sats
    forDf = {'filepath' : [], 'satellite?' : [],'minSeparation' : [], 'minTime' : [], 'csvPaths' : []}
    for key in files_affected_by_sats:

        forDf['filepath'].append(key) # add filename to df

        # check if it has satellites
        if len(files_affected_by_sats[key]) == 0:
            forDf['satellite?'].append(False)
            forDf['minSeparation'].append('N/A')
            forDf['minTime'].append('N/A')
            forDf['csvPaths'].append('N/A')
        else:
            forDf['satellite?'].append(True)
            forDf['minSeparation'].append(files_affected_by_sats[key][0])
            forDf['minTime'].append(files_affected_by_sats[key][1])
            forDf['csvPaths'].append(files_affected_by_sats[key][2])

    affectedFiles = pd.DataFrame(forDf)
    
    # Save the summary file to the work directory
    summary_file_path = os.path.join(work_dir, 'files_affected_by_sats.csv')
    affectedFiles.to_csv(summary_file_path)
    print(f"Summary saved to: {summary_file_path}")
    
    return affectedFiles

def main():
    '''
    dir [str] : directory that contains h5 files to check for satellites
                must end with a '/'
    '''

    #msg = f"Keys corresponding to GPS satellites to search for. Default keys are: 'Navigation/Global Positioning', 'Communication', 'Surveillance'. Other options include: {formattedKeys}"

    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', help='Directory with h5 files to run on', default=None)
    parser.add_argument('--file', help='File with list of h5 files to run on. If no dir is provided, will use this file', default=None)
    parser.add_argument('--pattern', help='input pattern to glob', default='*.h5')
    parser.add_argument('--plot', help='set to true to save plot of data', default=False)
    parser.add_argument('--n', help='higher n will be more inefficient', default=10)
    parser.add_argument('--work_dir', help='directory to store output files, defaults to current working directory', default=None)
    args = parser.parse_args()


    af = findSats(args.dir, args.file,  args.pattern, args.plot, args.n, work_dir=args.work_dir)
    affectedFiles = af.loc[af['minTime'] != 'N/A']#.drop_duplicates()
    
    # Set work directory for final output, default to current working directory
    work_dir = args.work_dir if args.work_dir else os.getcwd()
    os.makedirs(work_dir, exist_ok=True)
    final_output_path = os.path.join(work_dir, 'files_affected_by_sats.csv')
    affectedFiles.to_csv(final_output_path)


if __name__ == '__main__':
    sys.exit(main())
