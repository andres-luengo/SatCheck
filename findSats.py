'''
Modified from Chris Murphy's Satellite code
see: https://github.com/stevecroft/bl-interns/blob/master/chrismurphy/find_satellites.py
'''

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse

import ephem

from findSatsHelper import *

def findSats(dir, pattern, plot, key):

    # check that end of args.dir is a /
    if not dir[-1] == '/':
        dir += '/'

    # month conversion
    months = {"01":"jan", "02":"feb","03":"mar","04":"apr","05":"may","06":"jun",
                  "07":"jul","08":"aug","09":"sep","10":"oct","11":"nov", "12":"dec"}

    # read in the UCS Satellite Database for complete list of satellites
    df = pd.read_csv(queryUCS())

    # Get data from df depending on which keys we want to check
    if key:
        gps_data = df[df['Purpose'] == key]
    else:
        satsToCheck = ['Navigation/Global Positioning', 'Communication', 'Surveillance']
        toCheck = (df['Purpose'] == satsToCheck[0]) | (df['Purpose'] == satsToCheck[1]) | (df['Purpose'] == satsToCheck[2])
        gps_data = df[toCheck]

    gps_id_list = gps_data['NORAD Number'].tolist()

    # get comma separated string of relevant gps_ids to get the TLEs
    gps_ids = ''
    for i in gps_id_list:
        gps_ids = gps_ids + str(i) + ','

    # read in necessary info from the h5 files
    list_of_filenames = find_files(dir, pattern)
    start_time_mjd, ra_lst, dec_lst = pull_relevant_header_info(list_of_filenames)

    # get relevant TLEs
    tles = query_space_track(list_of_filenames, gps_ids)

    # Create ephem Observer object for GBT
    gbt = ephem.Observer()
    gbt.long = "-79.839857"
    gbt.lat = "38.432987"
    gbt.elevation = 807.0

    files_affected_by_sats = {}
    for (fil_file, ra, dec, dd) in zip(list_of_filenames, ra_lst, dec_lst, start_time_mjd):

        files_affected_by_sats[fil_file] = []

        date = convert(dd)
        year = date.split("-")[0]
        mon = date.split("-")[1]
        day1 = date.split("-")[2].split('T')[0]
        filename = months[mon] + '_' + day1 + "_" +year +"_TLEs.txt"

        # figure out which tle to compare to
        whichTLE = np.where(filename == tles)[0]
        tle = tles[whichTLE][0]

        # calculate the separation for 5 minutes after the start of observation
        if os.path.exists(filename):
            satdict = load_tle(tle)
            sat_hit_dict = separation(satdict, ra, dec, date, gbt)
        else:
            print('No satellites to crossmatch, exiting this check')
            break

        if len(sat_hit_dict.keys()) > 0:

            # write information to output files
            for stored_sats_in_obs, unique_sat_info in sat_hit_dict.items():

                outname = os.path.join(os.getcwd(), stored_sats_in_obs.replace(' ','_').replace('(','-').replace(')','-')+'_separation_'+fil_file.split('_')[-2] + '_' + fil_file.split('_')[-1]).replace('h5', 'csv')
                print('Writing to: ', outname)
                separationData = pd.DataFrame(unique_sat_info)
                separationData.to_csv(outname)

                minpoint = min(unique_sat_info['Separation'])

                minindex = unique_sat_info['Separation'].index(minpoint)
                mintime = unique_sat_info['Time after start'][minindex]

                if plot:
                    plotSeparation(unique_sat_info, stored_sats_in_obs, fil_file, mintime, minpoint, minindex)

                files_affected_by_sats[fil_file].append(minpoint)
                files_affected_by_sats[fil_file].append(mintime)

    # Write csv file of files affected and their minimum separation and time

    # unpack files_affected_by_sats
    forDf = {'filepath' : [], 'satellite?' : [],'minSeparation' : [], 'minTime' : []}
    for key in files_affected_by_sats:
        
        forDf['filepath'].append(key) # add filename to df

        # check if it has satellites
        if len(files_affected_by_sats[key]) == 0:
            forDf['satellite?'].append(False)
            forDf['minSeparation'].append('N/A')
            forDf['minTime'].append('N/A')
        else:
            forDf['satellite?'].append(True)
            forDf['minSeparation'].append(files_affected_by_sats[key][0])
            forDf['minTime'].append(files_affected_by_sats[key][1])

    affectedFiles = pd.DataFrame(forDf)
    affectedFiles.to_csv(os.path.join(os.getcwd(), 'files_affected_by_sats.csv'))

def main():
    '''
    dir [str] : directory that contains h5 files to check for satellites
                must end with a '/'
    '''

    # get input from command line user

    possibleKeys = ['Earth Observation', 'Technology Development', 'Communications',
       'Earth Science', 'Space Science',
       'Space Science/Technology Demonstration',
       'Communications/Technology Development',
       'Communications/Maritime Tracking', 'Technology Demonstration',
       'Navigation/Global Positioning',
       'Earth Observation/Technology Development', 'Signals Intelligence',
       'Earth Observation ', 'Earth Observation/Communications',
       'Space Observation', 'Earth/Space Observation', 'Educational',
       'Earth Observation/Earth Science', 'Platform',
       'Earth Observation/Space Science', 'Communications/Navigation',
       'Surveillance', 'Navigation/Regional Positioning',
       'Earth Observarion', 'Communication',
       'Space Science/Technology Development',
       'Mission Extension Technology', 'Earth Science/Earth Observation',
       'Unknown', 'Earth Observation/Communications/Space Science',
       'Technology Development/Educational', 'Satellite Positioning']

    formattedKeys = ""
    for k in possibleKeys:
        formattedKeys += k+', '

    msg = f"Keys corresponding to GPS satellites to search for. Default keys are: 'Navigation/Global Positioning', 'Communication', 'Surveillance'. Other options include: {formattedKeys}"

    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', help='Directory with h5 files to run on', default=os.getcwd())
    parser.add_argument('--pattern', help='input pattern to glob', default='*.h5')
    parser.add_argument('--plot', help='set to true to save plot of data', default=False)
    parser.add_argument('--key', help=msg, default=None)
    args = parser.parse_args()

    findSats(args.dir, args.pattern, args.plot, args.key)

if __name__ == '__main__':
    sys.exit(main())
