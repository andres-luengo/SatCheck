import os, sys, time, glob
import math
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from blimpy import Waterfall
from astropy.time import Time , TimeDelta
from datetime import datetime, date, timedelta
import ephem
from astropy import units as u
from astropy.coordinates import SkyCoord, EarthLocation, AltAz #,Angle
import requests
import urllib
from io import StringIO

'''
Following 10 functions taken from Chris Murphy's satellite code

see: https://github.com/stevecroft/bl-interns/blob/master/chrismurphy/find_satellites.py
'''

def find_files(inDir, inFile, fileList, pattern):
    '''
    Get all h5 files in input Directory
    inDir [str] : string of input directory
    pattern [str] : pattern to pass to glob

    return : list of h5 files to check for satellites
    '''

    if inDir is not None:
        toRet = glob.glob(inDir+pattern)
    elif inFile is not None:
        toRet = np.loadtxt(inFile, dtype=str)
    elif fileList is not None:
        toRet = fileList
    else:
        raise IOError('Please input either a directory housing h5 files or a file with a list of h5 paths')

    return toRet

def pull_relevant_header_info(filename_array):
    '''
    Read h5 header and pull out important info
    filename_array [array] : array of paths to check for satellites

    return : observation start time, target ra, target dec
    '''

    start_time_mjd_array =[]
    right_ascension_array = []
    declination_array = []

    for every_file in filename_array:

        # use blimpy to open h5 header
        wf = Waterfall(every_file, load_data=False)

        # get information and append to arrays to return
        start_time_mjd = wf.header['tstart']
        right_ascension = str(wf.header['src_raj'])
        declination = str(wf.header['src_dej'])

        start_time_mjd_array.append(start_time_mjd)
        right_ascension_array.append(right_ascension)
        declination_array.append(declination)

    return start_time_mjd_array, right_ascension_array, declination_array

def convert(mjd):
    '''
    Converts MJD time to isot for comparison
    mjd [str] : mjd date

    return : string start date in correct format
    '''
    startdate = Time(mjd, format='mjd')
    string_start_date = str(Time(startdate, format='isot'))
    return string_start_date

def query_space_track(fil_files, gps_ids, idx, overwrite=False, spacetrack_account=None, spacetrack_password=None, work_dir=None):
    '''
    Query space track to get TLEs
    fil_files [list] : list of input hdf5 files
    gps_ids [str] : comma separated string of gps ids to query for
    overwrite [bool] : default=False, set to True to overwrite space track files
    work_dir [str] : directory to store TLE files, defaults to current working directory

    return : array of TLE filenames
    '''

    if spacetrack_account is None:
        spacetrack_account = os.environ.get('SPACETRACK_ACCT')
    if spacetrack_account is None:
        raise ValueError('spacetrack_account must be passed in or environmental variable SPACETRACK_ACCT must be defined.')
    
    if spacetrack_password is None:
        spacetrack_password = os.environ.get('SPACETRACK_PASS')
    if spacetrack_password is None:
        raise ValueError('spacetrack_password must be passed in or environmental variable SPACETRACK_PASS must be defined.')

    print("Querying Space Track...")
    monthConversion = {"01":"jan", "02":"feb","03":"mar","04":"apr","05":"may","06":"jun",
                  "07":"jul","08":"aug","09":"sep","10":"oct","11":"nov", "12":"dec"}

    # Set work directory, default to current working directory
    if work_dir is None:
        work_dir = os.getcwd()
    
    # Ensure work_dir exists
    os.makedirs(work_dir, exist_ok=True)

    array_of_TLE_filenames = []
    for files in fil_files:

        # get important info from hdf5 header
        wf = Waterfall(files, load_data=False)

        # Format dates
        start_time_mjd = wf.header['tstart']
        mjd = Time(start_time_mjd, format='mjd')
        time_isot = Time(mjd, format='isot')
        day_change = TimeDelta(1 , format = 'jd')
        time_mjd_change = mjd + day_change
        time_isot_change = Time(time_mjd_change , format = 'isot')

        str_time1 = str(time_isot)
        str_time2 = str(time_isot_change)

        year_full_1 = str_time1.split("-")[0]
        year_full_2 = str_time2.split("-")[0]

        mon1 = str_time1.split("-")[1]
        day1 = str_time1.split("-")[2].split('T')[0]

        mon2 = str_time2.split("-")[1]
        day2 = str_time2.split("-")[2].split('T')[0]

        filename = os.path.join(work_dir, monthConversion[mon1] + "_" + day1 + '_' + year_full_1 + "_TLEs_" + str(idx) + ".txt")
        #print('Downloading TLEs to ', filename)

        if not os.path.isfile(filename) or overwrite: # only do next steps if file doesn't exist

            #Query space track for properly dated TLE info
            date1 = year_full_1+'-'+mon1+'-'+day1
            date2 = year_full_2+'-'+mon2+'-'+day2

            # Create a session for proper authentication
            session = requests.Session()
            
            # Login data for authentication
            login_data = {
                'identity': spacetrack_account,
                'password': spacetrack_password
            }
            
            try:
                # First authenticate to get session cookies
                login_response = session.post('https://www.space-track.org/ajaxauth/login', data=login_data)
                
                if login_response.status_code == 200:
                    # Check if login was actually successful by examining response
                    if 'Failed' in login_response.text or 'Login' in login_response.text:
                        print(f"Authentication failed for Space-Track.org. Login response indicates failure.")
                        continue
                        
                    # Now make the query using the authenticated session
                    # Format: class/tle for Two-Line Elements
                    query_url = f'https://www.space-track.org/basicspacedata/query/class/tle/EPOCH/{date1}--{date2}/NORAD_CAT_ID/{gps_ids}/orderby/TLE_LINE1 ASC/format/3le'
                    
                    print(f"Debug: Query URL: {query_url}")  # Debug output
                    
                    response = session.get(query_url)
                    
                    # Check if we got actual TLE data (not error messages)
                    response_text = response.content.decode('utf-8', errors='ignore')
                    
                    # Debug output
                    print(f"Debug: Response status: {response.status_code}")
                    print(f"Debug: Response length: {len(response_text)}")
                    print(f"Debug: Querying {len(gps_ids.split(','))} satellites for date range {date1} to {date2}")
                    if len(response_text) < 500:  # Print short responses for debugging
                        print(f"Debug: Response content preview: {response_text[:200]}")
                    
                    # Skip if response contains error messages or is empty
                    if (response.status_code == 200 and 
                        len(response_text.strip()) > 0 and 
                        'deprecated' not in response_text.lower() and
                        'error' not in response_text.lower() and
                        'unauthorized' not in response_text.lower() and
                        not response_text.strip().startswith('"') and
                        not response_text.strip().startswith('No records found')):
                        
                        print('######################################################################')
                        print("Downloading active GPS satellite TLEs from Space-Track: " , filename)
                        print('######################################################################')
                        
                        with open(filename, 'w+') as file:
                            file.write(response_text)
                    else:
                        print(f"Warning: No valid TLE data received for {filename}")
                        print(f"Response status: {response.status_code}")
                        if response.status_code == 204:
                            print("HTTP 204 means the query was valid but returned no data.")
                            print("This typically happens when:")
                            print("  - Satellites didn't exist during the requested time period")
                            print("  - SpaceTrack doesn't have historical TLE data for these satellites")
                            print("  - The date range is too specific for historical queries")
                        
                        # Don't try alternative query for 204 responses - they indicate no data available
                        if response.status_code != 204 and len(response_text) < 500:
                            print(f"Response content: {response_text}")
                        
                        # Only try alternative query if it's not a clear "no data" response
                        if response.status_code != 204 and (len(response_text.strip()) == 0 or response.status_code != 200):
                            print(f"Trying alternative query format for historical data...")
                            # Try querying with a broader time range or different approach
                            alt_query_url = f'https://www.space-track.org/basicspacedata/query/class/tle_latest/NORAD_CAT_ID/{gps_ids}/orderby/TLE_LINE1 ASC/format/3le'
                            print(f"Debug: Alternative query URL: {alt_query_url}")
                            
                            alt_response = session.get(alt_query_url)
                            alt_response_text = alt_response.content.decode('utf-8', errors='ignore')
                            
                            if (alt_response.status_code == 200 and 
                                len(alt_response_text.strip()) > 0 and
                                'deprecated' not in alt_response_text.lower() and
                                'error' not in alt_response_text.lower()):
                                
                                print(f"Alternative query succeeded, but data may not match exact date range.")
                                with open(filename, 'w+') as file:
                                    file.write(alt_response_text)
                else:
                    print(f"Authentication failed for Space-Track.org. Status code: {login_response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"Error querying Space-Track.org: {e}")
            finally:
                session.close()

            time.sleep(12.001)

        if filename not in array_of_TLE_filenames:
            array_of_TLE_filenames.append(filename)

    return np.array(array_of_TLE_filenames)


def load_tle(filename):
    '''
    Space Track is coming back with multiple TLEs for one satellite, with slightly different epochs
    Even when we download a TLE for that day, it comes back with two/three slightly different info
    Order satellites with ascending epoch, that way the last one we append to the dictionary
    has the most recent epoch and TLE info

    filename [str] : TLE file to open
    return : dictionary of relevant satellite information
    '''
    # Check if file exists and has content
    if not os.path.exists(filename):
        print(f"Warning: TLE file {filename} does not exist")
        return {}
    
    # open TLE file
    with open(filename, 'r') as f:
        content = f.read().strip()
    
    # Check if file is empty or contains only error messages
    if not content or len(content) == 0:
        print(f"Warning: TLE file {filename} is empty")
        return {}
    
    # Check for common error patterns
    if ('deprecated' in content.lower() or 
        content.startswith('"') or 
        'error' in content.lower()):
        print(f"Warning: TLE file {filename} contains error messages instead of TLE data")
        print(f"Content preview: {content[:200]}...")
        return {}
    
    satlist = []
    satdict = {}

    # Split content into lines
    lines = content.split('\n')
    
    # Process TLE data in groups of 3 lines
    i = 0
    while i < len(lines) - 2:
        l1 = lines[i].strip()
        l2 = lines[i + 1].strip()
        l3 = lines[i + 2].strip()
        
        # Skip empty lines
        if not l1 or not l2 or not l3:
            i += 1
            continue
        
        try:
            # Try to parse the TLE
            sat = ephem.readtle(l1, l2, l3)
            name = sat.name

            # Extract identity from line 3
            parts = l3.split()
            if len(parts) > 1:
                identity = parts[1]
                real_sat = name.replace('0 ', '') + ' ' + identity
                satdict[real_sat] = sat
                satlist.append(sat)
            
        except (ValueError, IndexError) as e:
            # Skip invalid TLE entries
            print(f"Warning: Skipping invalid TLE entry starting at line {i+1}: {e}")
            print(f"Lines: {l1[:50]}... {l2[:50]}... {l3[:50]}...")
        
        i += 3

    print(f"%i TLEs loaded from: %s" % (len(satlist), filename))
    return satdict

def separation(tle, ra_obs, dec_obs, start_time, gbt):
    '''
    Compute separation between satellite and target over 5 minute observation
    tle [] : TLE information
    ra_obs [float] : RA of observation
    dec_obs [float] : Dec of observation
    start_time [isot] : start time of observation
    gbt [ephem.Observer] : observation location

    return : dictionary of satellite hits
    '''

    # Format input values
    sat_hit_dict = {}
    ra_obs = ra_obs.replace('h', ':').replace('m', ':').replace('s', '')
    dec_obs = dec_obs.replace('d', ':').replace('m',':').replace('s','')

    dec_obs = ephem.degrees(dec_obs)
    ra_obs = ephem.hours(ra_obs)

    for unique_sats, satellite_object in tle.items():

        ra = []
        dec = []
        close_sats = []
        close_sep = []
        close_time = []
        time_after = []
        unique_sat_name = {}
        time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%f")
        time_after_start = 0

        for delta_time in range(0,300):

            time += timedelta(seconds = 1) # increment time
            time_after_start += 1
            gbt.date = time
            satellite_object.compute(gbt)
            sat_ra, sat_dec = str(satellite_object.ra) , str(satellite_object.dec)

            sep = ephem.separation((satellite_object.ra, satellite_object.dec), (ra_obs , dec_obs))

            sep_rad = repr(sep)

            sep_deg = np.rad2deg(float(sep_rad))

            if sep_deg < 3:

                # get important info if the separation is less than 3 for an observation
                ra.append(sat_ra)
                dec.append(sat_dec)
                close_sep.append(sep_deg)
                close_time.append(time)
                time_after.append(time_after_start)
                unique_sat_name['RA'] = ra
                unique_sat_name['DEC'] = dec
                unique_sat_name['Separation'] = close_sep
                unique_sat_name['Time after start'] = time_after
                sat_hit_dict[unique_sats] = unique_sat_name
                if satellite_object not in close_sats:
                    close_sats.append(satellite_object)

    return sat_hit_dict


'''
Now the rest of these functions I wrote
'''

def queryUCS(work_dir=None):
    '''
    Queries the UCS Satellite Database and downloads the most up to date file info
    work_dir [str] : directory to store database file, defaults to current working directory

    returns : path to the downloaded file
    '''

    print('Downloading newest UCS Satellite Database File')

    # Set work directory, default to current working directory
    if work_dir is None:
        work_dir = os.getcwd()
    
    # Ensure work_dir exists
    os.makedirs(work_dir, exist_ok=True)

    url = 'https://www.ucsusa.org/sites/default/files/2021-11/UCS-Satellite-Database-9-1-2021.txt'
    outPath = os.path.join(work_dir, 'UCS-Satellite-Database.txt')

    req = urllib.request.Request(url, headers={'User-Agent' : 'Mozilla/5.0'})
    ucsData = urllib.request.urlopen(req).read()

    strUCS = ucsData.decode('cp1252')
    dataArr = [s.split('\t') for s in strUCS.split('\n')]
    parsedData = pd.DataFrame(dataArr[1:], columns=dataArr[0])

    parsedData.to_csv(outPath)

    return outPath

def plotSeparation(unique_sat_info, stored_sats_in_obs, fil_file, mintime, minpoint, minindex, work_dir=None):
    '''
    plots separation between satellite and target
    work_dir [str] : directory to save plot files, defaults to current working directory
    '''

    # Set work directory, default to current working directory
    if work_dir is None:
        work_dir = os.getcwd()
    
    # Ensure work_dir exists
    os.makedirs(work_dir, exist_ok=True)

    plt.scatter(unique_sat_info['Separation'], unique_sat_info['Time after start'], s = 1, label = stored_sats_in_obs)

    print("++++++++++++++++++++++")
    print(minindex , mintime , minpoint)
    print("++++++++++++++++++++++++")
    print("++++++++++++++++++++++++\n\n")
    #plt.hlines(y=minpoint, xmin = 1, xmax = 300, label = 'Minpoint: ' + str(minpoint))
    #plt.hlines(unique_sat_info['Time after start'], unique_sat_info['Separation'], lw = 2, label = minpoint)
    plt.scatter(minpoint, mintime, s = 10, label = 'Min: ' + str("%.5fdeg " % minpoint) + str(mintime) + "s")
    ymax = ephem.degrees('03:00:00')
    ymax_rad = repr(ymax)

    ymax_deg = np.rad2deg(float(ymax_rad))

    plt.ylabel('Time after start (seconds)')
    plt.xlabel('Separation (degrees)')
    plt.ylim(0, 300)
    plt.xlim(0, ymax_deg)
    plot_name = fil_file.split('_')[-2] + '_' + fil_file.split('_')[-1]
    plt.title(plot_name)
    plt.legend()
    plot_file_path = os.path.join(work_dir, plot_name + '_time_sep_.png')
    plt.savefig(plot_file_path, transparent=False)
