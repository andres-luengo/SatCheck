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
    Get NORAD IDs from UCS database, filtered for satellites likely to have historical data.
    
    This function downloads the UCS (Union of Concerned Scientists) Satellite Database
    and extracts NORAD catalog numbers for satellites that are likely to have historical
    TLE (Two-Line Element) data available from Space-Track.org.
    
    Parameters
    ----------
    n : int
        Number of partitions to split the satellite ID list into for efficient querying.
        Higher values may be less efficient for Space Track API calls.
    work_dir : str, optional
        Directory to store downloaded database files. If None, uses current working directory.
        
    Returns
    -------
    list of numpy.ndarray
        List containing n arrays, each with NORAD catalog numbers for querying.
        The arrays are roughly equal in size to balance query loads.
        
    Notes
    -----
    The function filters satellites to focus on those launched before 2022, as these
    are more likely to have historical TLE data available for retrospective analysis
    of older observation data.
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
    """
    Download Two-Line Element (TLE) data from Space-Track.org for satellite analysis.
    
    This function queries the Space-Track.org database to download TLE data for all
    satellites that might interfere with radio astronomy observations. It partitions
    the satellite catalog into manageable chunks and downloads TLEs for the time
    periods corresponding to the input observation files.
    
    Parameters
    ----------
    list_of_filenames : list of str
        List of HDF5 file paths containing radio astronomy observation data.
        The observation timestamps from these files determine the TLE query dates.
    n : int
        Number of partitions to split the satellite catalog into for efficient querying.
        Typically 10 is optimal; lower values may overload Space-Track.org API.
    spacetrack_account : str, optional
        Space-Track.org account username (usually email address).
        If None, reads from SPACETRACK_ACCT environment variable.
    spacetrack_password : str, optional
        Space-Track.org account password.
        If None, reads from SPACETRACK_PASS environment variable.
    work_dir : str, optional
        Directory to store downloaded TLE files and temporary data.
        If None, uses current working directory.
        
    Returns
    -------
    numpy.ndarray
        Array of file paths to the combined TLE files, one per unique observation date.
        These files contain TLE data for all satellites active during each observation.
        
    Raises
    ------
    ValueError
        If Space-Track.org credentials are not provided via parameters or environment variables.
        
    Notes
    -----
    - Requires valid Space-Track.org account credentials
    - Downloads are rate-limited to comply with Space-Track.org API policies  
    - TLE files are cached locally to avoid repeated downloads for the same dates
    - Files are named using the format: {month}_{day}_{year}_TLEs.txt
    """

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
    """
    Identify satellite interference in radio astronomy observation data.
    
    This is the main function of the SatCheck package. It analyzes HDF5 observation files
    to detect potential satellite interference by comparing observation coordinates and
    times with satellite orbital data from Space-Track.org. The function computes
    angular separations between satellites and observation targets over time.
    
    Parameters
    ----------
    dir : str, optional
        Directory containing HDF5 observation files to analyze.
        Must end with '/' if provided. Mutually exclusive with `file` and `file_list`.
    file : str, optional  
        Path to text file containing list of HDF5 file paths to analyze.
        Mutually exclusive with `dir` and `file_list`.
    pattern : str, default='*.h5'
        Glob pattern for finding HDF5 files when using `dir` parameter.
        Examples: '*.h5', '*0000.h5', 'target_*.h5'
    plot : bool, default=False
        Whether to generate separation plots for each satellite pass.
        Creates time vs. angular separation plots for visual inspection.
    n : int, default=10
        Number of partitions for satellite catalog queries. Lower values may
        overload Space-Track.org API. Do not change unless you understand the implications.
    file_list : list of str, optional
        Direct list of HDF5 file paths to analyze.
        Mutually exclusive with `dir` and `file`.
    spacetrack_account : str, optional
        Space-Track.org username. If None, uses SPACETRACK_ACCT environment variable.
    spacetrack_password : str, optional
        Space-Track.org password. If None, uses SPACETRACK_PASS environment variable.
    work_dir : str, optional
        Directory for storing output files (TLEs, CSVs, plots).
        If None, uses current working directory.
        
    Returns
    -------
    pandas.DataFrame
        Summary DataFrame with columns:
        - 'filepath': Path to each analyzed observation file
        - 'satellite?': Boolean indicating if satellites were detected
        - 'minSeparation': List of minimum angular separations for each satellite (degrees)
        - 'minTime': List of times when minimum separations occurred (seconds after start)
        - 'csvPaths': List of paths to detailed separation CSV files
        
    Raises
    ------
    IOError
        If none of `dir`, `file`, or `file_list` parameters are provided.
    ValueError
        If Space-Track.org credentials are missing.
        
    Notes
    -----
    - Requires Space-Track.org account for TLE data access
    - Considers satellites within 3 degrees of target as potential interference
    - Analyzes 5-minute observation windows starting from file timestamp
    - Creates detailed CSV files for each satellite pass detected
    - Observation coordinates are read from HDF5 file headers (src_raj, src_dej)
    - Uses Green Bank Telescope coordinates as observation site
    
    Examples
    --------
    Analyze all HDF5 files in a directory:
    
    >>> results = findSats(dir="/data/observations/", work_dir="/output/")
    
    Analyze specific files from a list:
    
    >>> file_list = ["obs1.h5", "obs2.h5"] 
    >>> results = findSats(file_list=file_list, plot=True)
    
    Use file containing list of observations:
    
    >>> results = findSats(file="observation_list.txt")
    """

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
        
        # Construct full path for filename matching
        full_filename = os.path.join(work_dir, filename)

        # figure out which tle to compare to
        whichTLE = np.where(full_filename == tles)[0]

        # calculate the separation for 5 minutes after the start of observation
        if len(whichTLE) > 0 and os.path.exists(full_filename):
            tle = tles[whichTLE][0]
            satdict = load_tle(tle)
            sat_hit_dict = separation(satdict, ra, dec, date, gbt)
        else:
            print(f'No satellites to crossmatch for {filename}, skipping this observation')
            print(f'Expected file: {full_filename}')
            print(f'Available TLE files: {[os.path.basename(t) for t in tles[:5]]}...')  # Show first 5 for debugging
            continue

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
