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

from findSatsHelper import *
from genPlotsAll import plotSep

def io(n):

    # read in the UCS Satellite Database for complete list of satellites
    df = pd.read_csv(queryUCS())

    idList = np.array(df['NORAD Number'].tolist())

    return np.array_split(idList, n)

def downloadTLEs(list_of_filenames, n):

    noradIds = io(n)

    # get relevant TLEs
    allTLEfiles = []
    for idx, nIds in enumerate(noradIds):
        # get comma separated string of relevant ids to get the TLEs
        ids = ''
        for i in nIds:
            ids = ids + str(i) + ','
        tles = query_space_track(list_of_filenames, ids, idx)
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

    for key in sepTLEs.keys():
        with open(f"{key}.txt", "wb") as outfile:
            for f in sepTLEs[key]:
                if os.path.exists(f):
                    with open(f, "rb") as infile:
                        outfile.write(infile.read())

                    os.remove(f)

    return np.array([name+'.txt' for name in baseNames])

def findSats(dir, file, pattern, plot, n):

    # check that end of args.dir is a /
    if dir != None and not dir[-1] == '/':
        dir += '/'

    # month conversion
    months = {"01":"jan", "02":"feb","03":"mar","04":"apr","05":"may","06":"jun",
                  "07":"jul","08":"aug","09":"sep","10":"oct","11":"nov", "12":"dec"}

    # read in necessary info from the h5 files
    list_of_filenames = find_files(dir, file, pattern)
    start_time_mjd, ra_lst, dec_lst = pull_relevant_header_info(list_of_filenames)

    tles = downloadTLEs(list_of_filenames, n)

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

                outname = os.path.join(os.getcwd(), stored_sats_in_obs.replace(' ','_').replace('(','-').replace(')','-').replace('/', '-')+'_separation_'+fil_file.split('_')[-2] + '_' + fil_file.split('_')[-1]).replace('h5', 'csv')

                if not os.path.exists(outname):

                    print('Writing to: ', outname)
                    separationData = pd.DataFrame(unique_sat_info)
                    separationData.to_csv(outname)

                minpoint = min(unique_sat_info['Separation'])

                minindex = unique_sat_info['Separation'].index(minpoint)
                mintime = unique_sat_info['Time after start'][minindex]

                if plot:
                    plotSep(outname)
                    #plotSeparation(unique_sat_info, stored_sats_in_obs, fil_file, mintime, minpoint, minindex)

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
    args = parser.parse_args()


    af = findSats(args.dir, args.file,  args.pattern, args.plot, args.n)
    affectedFiles = af.loc[af['minTime'] != 'N/A']#.drop_duplicates()
    affectedFiles.to_csv(os.path.join(os.getcwd(), 'files_affected_by_sats.csv'))


if __name__ == '__main__':
    sys.exit(main())
