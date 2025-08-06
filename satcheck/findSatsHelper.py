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
    """
    Get list of HDF5 files to analyze from various input sources.
    
    This function provides flexible input handling for specifying which observation
    files to process. It accepts either a directory to search, a file containing
    a list of paths, or a direct list of file paths.
    
    Parameters
    ----------
    inDir : str or None
        Directory path to search for files using glob pattern.
        Should end with '/' for consistency.
    inFile : str or None  
        Path to text file containing list of HDF5 file paths, one per line.
    fileList : list of str or None
        Direct list of HDF5 file paths to process.
    pattern : str
        Glob pattern for finding files in inDir (e.g., '*.h5', '*0000.h5').
        
    Returns
    -------
    list or numpy.ndarray
        List of HDF5 file paths to analyze for satellite interference.
        
    Raises
    ------
    IOError
        If none of the input parameters (inDir, inFile, fileList) are provided.
        
    Notes
    -----
    Parameters are mutually exclusive - only one should be provided:
    - inDir: Search directory with glob pattern
    - inFile: Read file list from text file  
    - fileList: Use provided list directly
    
    Examples
    --------
    Search directory for all HDF5 files:
    
    >>> files = find_files("/data/obs/", None, None, "*.h5")
    
    Load file list from text file:
    
    >>> files = find_files(None, "file_list.txt", None, None)
    
    Use direct file list:
    
    >>> files = find_files(None, None, ["obs1.h5", "obs2.h5"], None)
    """

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
    """
    Extract observation parameters from HDF5 file headers.
    
    This function reads essential observation metadata from Breakthrough Listen
    HDF5 files, including observation start times and target coordinates.
    These parameters are needed for satellite interference calculations.
    
    Parameters
    ----------
    filename_array : list of str
        List of paths to HDF5 observation files to process.
        
    Returns
    -------
    tuple of (list, list, list)
        Three lists containing:
        - start_time_mjd_array : Modified Julian Date start times for each observation
        - right_ascension_array : Right ascension coordinates (J2000) as strings  
        - declination_array : Declination coordinates (J2000) as strings
        
    Notes
    -----
    - Uses blimpy library to read HDF5 headers without loading data
    - Coordinates are extracted in the format used by the observation system
    - Start times are in Modified Julian Date (MJD) format
    - Header fields read: 'tstart', 'src_raj', 'src_dej'
    
    Examples
    --------
    Extract info from observation files:
    
    >>> files = ["obs1.h5", "obs2.h5"]
    >>> times, ra_list, dec_list = pull_relevant_header_info(files)
    >>> print(f"First observation: RA={ra_list[0]}, Dec={dec_list[0]}")
    """

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
    """
    Convert Modified Julian Date to ISO format string.
    
    This function converts observation timestamps from Modified Julian Date (MJD)
    format to ISO 8601 format for compatibility with satellite orbital calculations
    and TLE queries.
    
    Parameters
    ----------
    mjd : float
        Modified Julian Date timestamp from observation header.
        
    Returns
    -------
    str
        ISO 8601 formatted date-time string (YYYY-MM-DDTHH:MM:SS.ffffff).
        
    Notes
    -----
    Uses astropy.time.Time for accurate astronomical time conversions.
    The output format is compatible with ephem library calculations.
    
    Examples
    --------
    Convert MJD to ISO format:
    
    >>> iso_time = convert(58849.5)
    >>> print(iso_time)  # "2020-01-15T12:00:00.000"
    """
    startdate = Time(mjd, format='mjd')
    string_start_date = str(Time(startdate, format='isot'))
    return string_start_date

def query_space_track(fil_files, gps_ids, idx, overwrite=False, spacetrack_account=None, spacetrack_password=None, work_dir=None):
    """
    Download Two-Line Element (TLE) data from Space-Track.org for specific satellites and dates.
    
    This function queries the Space-Track.org database to download historical TLE data
    for specified satellites during the time periods of radio astronomy observations.
    It handles authentication, rate limiting, and error handling for the Space-Track API.
    
    Parameters
    ----------
    fil_files : list of str
        List of HDF5 observation file paths. Observation dates from these files
        determine the TLE query date ranges.
    gps_ids : str
        Comma-separated string of NORAD catalog IDs for satellites to query.
        Example: "12345,67890,54321"
    idx : int
        Index number for output filename uniqueness when processing multiple batches.
    overwrite : bool, default=False
        Whether to overwrite existing TLE files. If False, skips download if file exists.
    spacetrack_account : str, optional
        Space-Track.org account username (typically email address).
        If None, uses SPACETRACK_ACCT environment variable.
    spacetrack_password : str, optional
        Space-Track.org account password.
        If None, uses SPACETRACK_PASS environment variable.
    work_dir : str, optional
        Directory to save TLE files. If None, uses current working directory.
        
    Returns
    -------
    numpy.ndarray
        Array of file paths to downloaded TLE files, one per unique observation date.
        
    Raises
    ------
    ValueError
        If Space-Track.org credentials are not provided via parameters or environment variables.
        
    Notes
    -----
    - Requires valid Space-Track.org account (free registration required)
    - Implements 12-second delays between queries to respect API rate limits
    - Downloads TLEs for observation date ±1 day to ensure coverage
    - Files are named: {month}_{day}_{year}_TLEs_{idx}.txt
    - Handles various API response codes and error conditions gracefully
    - Falls back to latest TLE queries if historical data is unavailable
    
    Examples
    --------
    Query TLEs for specific satellites:
    
    >>> files = ["obs_2020_01_15.h5"]
    >>> satellite_ids = "25544,20580,27424"  # ISS, GPS satellites
    >>> tle_files = query_space_track(files, satellite_ids, 0, 
    ...                              spacetrack_account="user@email.com",
    ...                              spacetrack_password="password")
    """

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
    """
    Parse Two-Line Element (TLE) data from Space-Track.org files into satellite objects.
    
    This function reads TLE files downloaded from Space-Track.org and converts them
    into PyEphem satellite objects for orbital calculations. It handles multiple TLEs
    per satellite and selects the most recent epoch for each satellite.
    
    Parameters
    ----------
    filename : str
        Path to TLE file downloaded from Space-Track.org.
        File should contain TLE data in standard 3-line format.
        
    Returns
    -------
    dict
        Dictionary mapping satellite names to PyEphem satellite objects.
        Keys are satellite names with catalog IDs, values are ephem.EarthSatellite objects.
        Returns empty dict if file is missing, empty, or contains errors.
        
    Notes
    -----
    - TLE format: 3 lines per satellite (name, line1, line2)
    - Handles multiple TLEs per satellite by keeping the most recent epoch
    - Filters out invalid TLE entries and error responses from Space-Track
    - Satellite names are formatted as "NAME CATALOG_ID" for uniqueness
    - Uses PyEphem library for satellite object creation and orbital calculations
    
    Examples
    --------
    Load satellites from TLE file:
    
    >>> satellites = load_tle("jan_15_2020_TLEs.txt")
    >>> print(f"Loaded {len(satellites)} satellites")
    >>> for name, sat in satellites.items():
    ...     print(f"Satellite: {name}")
    
    Check if specific satellite is loaded:
    
    >>> if "ISS (ZARYA) 25544" in satellites:
    ...     iss = satellites["ISS (ZARYA) 25544"]
    """
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
    """
    Calculate angular separation between satellites and observation target over time.
    
    This function computes the angular separation between each satellite and the
    observation target coordinates for a 5-minute observation period. It identifies
    satellites that pass within 3 degrees of the target as potential interference sources.
    
    Parameters
    ----------
    tle : dict
        Dictionary of satellite objects from load_tle(), mapping names to ephem satellites.
    ra_obs : str
        Right ascension of observation target in format "XXhYYmZZs" (hours, minutes, seconds).
    dec_obs : str  
        Declination of observation target in format "±XXdYYmZZs" (degrees, minutes, seconds).
    start_time : str
        Observation start time in ISO format "YYYY-MM-DDTHH:MM:SS.fff".
    gbt : ephem.Observer
        PyEphem observer object representing the observation site location.
        
    Returns
    -------
    dict
        Dictionary mapping satellite names to separation data for satellites that
        pass within 3 degrees of the target. Each entry contains:
        - 'RA': List of satellite RA positions during close approaches
        - 'DEC': List of satellite declination positions  
        - 'Separation': List of angular separations in degrees
        - 'Time after start': List of time offsets in seconds from observation start
        
    Notes
    -----
    - Analyzes 300 seconds (5 minutes) of satellite motion at 1-second intervals
    - Only includes satellites that come within 3 degrees of the target
    - Uses PyEphem for accurate satellite position calculations
    - Observer location affects satellite visibility and positions
    - Angular separations calculated using great circle distance
    
    Examples
    --------
    Calculate separations for loaded satellites:
    
    >>> satellites = load_tle("tle_file.txt")
    >>> gbt = ephem.Observer()
    >>> gbt.long, gbt.lat = "-79.839857", "38.432987"  # Green Bank
    >>> close_sats = separation(satellites, "12h30m45s", "+41d16m09s", 
    ...                        "2020-01-15T14:30:00.000", gbt)
    >>> for sat_name, data in close_sats.items():
    ...     min_sep = min(data['Separation'])
    ...     print(f"{sat_name}: minimum separation {min_sep:.3f} degrees")
    """

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
    """
    Download the Union of Concerned Scientists (UCS) Satellite Database.
    
    This function downloads the most recent UCS Satellite Database, which contains
    comprehensive information about active satellites including NORAD catalog numbers,
    launch dates, and satellite classifications. This database is used as the source
    for satellite IDs to query from Space-Track.org.
    
    Parameters
    ----------
    work_dir : str, optional
        Directory to save the downloaded database file.
        If None, uses current working directory.
        
    Returns
    -------
    str
        Path to the downloaded and processed CSV database file.
        
    Notes
    -----
    - Downloads from UCS website (https://www.ucsusa.org)
    - Converts original tab-separated format to CSV for easier processing
    - File is saved as 'UCS-Satellite-Database.txt' in the work directory
    - Database includes satellites from various countries and organizations
    - Used as master catalog for satellite ID queries to Space-Track.org
    - Database is typically updated annually by UCS
    
    Examples
    --------
    Download UCS database to current directory:
    
    >>> db_path = queryUCS()
    >>> print(f"Database saved to: {db_path}")
    
    Download to specific directory:
    
    >>> db_path = queryUCS(work_dir="/data/satellite_db/")
    >>> import pandas as pd
    >>> satellites = pd.read_csv(db_path)
    >>> print(f"Database contains {len(satellites)} satellites")
    """

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
    """
    Generate a scatter plot of satellite angular separation vs. time.
    
    This function creates a visualization showing how the angular separation between
    a satellite and the observation target changes over the 5-minute observation window.
    The plot highlights the minimum separation point for easy identification.
    
    Parameters
    ----------
    unique_sat_info : dict
        Dictionary containing satellite separation data with keys:
        - 'Separation': List of angular separations in degrees
        - 'Time after start': List of time offsets in seconds
    stored_sats_in_obs : str
        Name of the satellite for plot labeling.
    fil_file : str
        Name of the observation file for plot title generation.
    mintime : float
        Time (seconds after start) when minimum separation occurred.
    minpoint : float
        Minimum angular separation value in degrees.
    minindex : int
        Index in the data arrays where minimum separation occurred.
    work_dir : str, optional
        Directory to save the plot file. If None, uses current working directory.
        
    Notes
    -----
    - Creates scatter plot with separation on x-axis, time on y-axis
    - Highlights minimum separation point with special marker and annotation
    - Plot limits: time 0-300 seconds, separation 0-3 degrees
    - Saves as PNG file with name based on observation file
    - Uses matplotlib for plotting and figure generation
    
    Examples
    --------
    Plot separation data for a satellite pass:
    
    >>> sat_data = {
    ...     'Separation': [2.5, 2.1, 1.8, 2.0, 2.4],
    ...     'Time after start': [60, 120, 180, 240, 300]
    ... }
    >>> plotSeparation(sat_data, "GPS BIIR-2 13833", "obs_file.h5",
    ...               180, 1.8, 2, work_dir="/plots/")
    """

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
