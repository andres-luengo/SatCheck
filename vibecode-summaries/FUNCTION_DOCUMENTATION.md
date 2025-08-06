# SatCheck Function Documentation

This document provides comprehensive documentation for all front-facing functions in the SatCheck package, organized by module.

## Table of Contents

1. [Main Functions](#main-functions)
2. [Helper Functions](#helper-functions) 
3. [Plotting Functions](#plotting-functions)
4. [GPS Analysis Functions](#gps-analysis-functions)
5. [Usage Examples](#usage-examples)

## Main Functions

### `findSats()`

**Location**: `satcheck.findSats`

**Purpose**: Main function for identifying satellite interference in radio astronomy observation data.

**Parameters**:
- `dir` (str, optional): Directory containing HDF5 observation files
- `file` (str, optional): Path to text file with list of HDF5 files
- `pattern` (str, default='*.h5'): Glob pattern for finding files
- `plot` (bool, default=False): Generate separation plots
- `n` (int, default=10): Number of partitions for satellite queries
- `file_list` (list, optional): Direct list of HDF5 file paths
- `spacetrack_account` (str, optional): Space-Track.org username
- `spacetrack_password` (str, optional): Space-Track.org password
- `work_dir` (str, optional): Output directory

**Returns**: pandas.DataFrame with satellite detection results

**Example**:
```python
import satcheck

# Analyze directory of observations
results = satcheck.findSats(
    dir="/data/observations/",
    plot=True,
    work_dir="/output/satellite_analysis/"
)

# Check results
affected = results[results['satellite?'] == True]
print(f"Found satellite interference in {len(affected)} observations")
```

### `io()`

**Location**: `satcheck.findSats`

**Purpose**: Extract NORAD satellite IDs from UCS database for TLE queries.

**Parameters**:
- `n` (int): Number of partitions for the satellite ID list
- `work_dir` (str, optional): Directory for database files

**Returns**: List of numpy arrays containing NORAD catalog numbers

### `downloadTLEs()`

**Location**: `satcheck.findSats`

**Purpose**: Download Two-Line Element data from Space-Track.org.

**Parameters**:
- `list_of_filenames` (list): HDF5 observation files
- `n` (int): Number of satellite ID partitions
- `spacetrack_account` (str, optional): Space-Track.org username
- `spacetrack_password` (str, optional): Space-Track.org password
- `work_dir` (str, optional): Output directory

**Returns**: numpy.ndarray of TLE file paths

## Helper Functions

### `find_files()`

**Location**: `satcheck.findSatsHelper`

**Purpose**: Get list of HDF5 files from various input sources.

**Parameters**:
- `inDir` (str or None): Directory to search
- `inFile` (str or None): File containing list of paths
- `fileList` (list or None): Direct list of file paths
- `pattern` (str): Glob pattern for directory search

**Returns**: List of HDF5 file paths

### `pull_relevant_header_info()`

**Location**: `satcheck.findSatsHelper`

**Purpose**: Extract observation parameters from HDF5 headers.

**Parameters**:
- `filename_array` (list): List of HDF5 file paths

**Returns**: Tuple of (start_times, ra_coordinates, dec_coordinates)

### `convert()`

**Location**: `satcheck.findSatsHelper`

**Purpose**: Convert Modified Julian Date to ISO format.

**Parameters**:
- `mjd` (float): Modified Julian Date timestamp

**Returns**: ISO 8601 formatted date-time string

### `query_space_track()`

**Location**: `satcheck.findSatsHelper`

**Purpose**: Download TLE data from Space-Track.org for specific satellites.

**Parameters**:
- `fil_files` (list): HDF5 observation files
- `gps_ids` (str): Comma-separated NORAD catalog IDs
- `idx` (int): Index for filename uniqueness
- `overwrite` (bool, default=False): Overwrite existing files
- `spacetrack_account` (str, optional): Space-Track.org username
- `spacetrack_password` (str, optional): Space-Track.org password
- `work_dir` (str, optional): Output directory

**Returns**: numpy.ndarray of TLE file paths

### `load_tle()`

**Location**: `satcheck.findSatsHelper`

**Purpose**: Parse TLE files into satellite objects.

**Parameters**:
- `filename` (str): Path to TLE file

**Returns**: Dictionary mapping satellite names to PyEphem objects

### `separation()`

**Location**: `satcheck.findSatsHelper`

**Purpose**: Calculate angular separation between satellites and observation targets.

**Parameters**:
- `tle` (dict): Dictionary of satellite objects
- `ra_obs` (str): Target right ascension
- `dec_obs` (str): Target declination
- `start_time` (str): Observation start time
- `gbt` (ephem.Observer): Observer location

**Returns**: Dictionary of satellite separation data for close approaches

### `queryUCS()`

**Location**: `satcheck.findSatsHelper`

**Purpose**: Download UCS Satellite Database.

**Parameters**:
- `work_dir` (str, optional): Output directory

**Returns**: Path to downloaded database file

### `plotSeparation()`

**Location**: `satcheck.findSatsHelper`

**Purpose**: Generate scatter plot of satellite separation vs. time.

**Parameters**:
- `unique_sat_info` (dict): Separation data
- `stored_sats_in_obs` (str): Satellite name
- `fil_file` (str): Observation file name
- `mintime` (float): Time of minimum separation
- `minpoint` (float): Minimum separation value
- `minindex` (int): Index of minimum separation
- `work_dir` (str, optional): Output directory

## Plotting Functions

### `plotH5()`

**Location**: `satcheck.genPlotsAll`

**Purpose**: Generate waterfall plot of observation data.

**Parameters**:
- `satCsv` (list): List of satellite separation CSV files
- `h5Path` (str): Path to HDF5 observation file
- `memLim` (int, default=20): Memory limit in GB
- `work_dir` (str, optional): Output directory

**Example**:
```python
import satcheck

# Plot observation with satellite context
satcheck.plotH5(
    ["GPS_satellite_separation.csv"],
    "observation_lband.h5",
    memLim=40,
    work_dir="/plots/"
)
```

### `plotSep()`

**Location**: `satcheck.genPlotsAll`

**Purpose**: Generate line plot of satellite separation over time.

**Parameters**:
- `satCsv` (str): Path to separation CSV file
- `work_dir` (str, optional): Output directory

**Example**:
```python
import satcheck

# Plot satellite separation data
satcheck.plotSep("GPS_BIIR-2_separation_target123.csv")
```

### `band()`

**Location**: `satcheck.genPlotsAll`

**Purpose**: Determine frequency band of observation file.

**Parameters**:
- `file` (str): Path to HDF5 file
- `tol` (float, default=0.7): Tolerance for band matching

**Returns**: List of [min_freq, max_freq] or "NA"

### `decryptSepName()`

**Location**: `satcheck.genPlotsAll`

**Purpose**: Extract satellite and target names from CSV filename.

**Parameters**:
- `path` (str): Path to separation CSV file

**Returns**: Tuple of (satellite_name, target_name)

## GPS Analysis Functions

### `findGPSTargs()`

**Location**: `satcheck.findGPSFiles`

**Purpose**: Find observations with GPS L1 band interference.

**Parameters**:
- `e` (float): Frequency tolerance in MHz around 1600 MHz

**Returns**: List of file names with GPS interference

**Example**:
```python
import satcheck

# Find files with GPS L1 interference (±10 MHz)
gps_affected_files = satcheck.findGPSTargs(10.0)
print(f"Found {len(gps_affected_files)} GPS-affected observations")
```

## Usage Examples

### Basic Satellite Detection

```python
import satcheck
import os

# Set up Space-Track.org credentials (or use environment variables)
os.environ['SPACETRACK_ACCT'] = 'your_email@domain.com'
os.environ['SPACETRACK_PASS'] = 'your_password'

# Analyze observations in a directory
results = satcheck.findSats(
    dir="/data/breakthrough_listen/observations/",
    pattern="*.h5",
    plot=True,
    work_dir="/analysis/satellite_check/"
)

# Check for affected observations
affected = results[results['satellite?'] == True]
print(f"Satellite interference detected in {len(affected)} files")

# Get minimum separations
for idx, row in affected.iterrows():
    min_seps = row['minSeparation']
    if min_seps != 'N/A':
        closest = min([min(sep_list) for sep_list in min_seps])
        print(f"File: {row['filepath']}, Closest satellite: {closest:.3f} degrees")
```

### Processing File Lists

```python
# Create list of specific observations to analyze
observation_files = [
    "/data/obs/target1_timestamp1.h5",
    "/data/obs/target1_timestamp2.h5", 
    "/data/obs/target2_timestamp1.h5"
]

# Analyze specific files
results = satcheck.findSats(
    file_list=observation_files,
    work_dir="/analysis/targeted_search/"
)
```

### Generating Plots

```python
import pandas as pd

# Load results from previous analysis
results = pd.read_csv("/analysis/satellite_check/files_affected_by_sats.csv")

# Generate plots for affected observations
for idx, row in results.iterrows():
    if row['satellite?']:
        # Generate waterfall plot
        satcheck.plotH5(
            row['csvPaths'],
            row['filepath'],
            memLim=50,
            work_dir="/plots/"
        )
        
        # Generate separation plots for each satellite
        for csv_path in row['csvPaths']:
            satcheck.plotSep(csv_path, work_dir="/plots/")
```

### Advanced Usage with Custom Parameters

```python
# Custom analysis with specific parameters
results = satcheck.findSats(
    dir="/data/x_band_observations/",
    pattern="*xband*.h5",
    n=5,  # Fewer partitions for smaller dataset
    plot=True,
    spacetrack_account="custom_account@email.com",
    spacetrack_password="custom_password",
    work_dir="/analysis/xband_satellites/"
)

# Process results
summary_stats = {
    'total_files': len(results),
    'affected_files': len(results[results['satellite?'] == True]),
    'clean_files': len(results[results['satellite?'] == False])
}

print("Analysis Summary:")
for key, value in summary_stats.items():
    print(f"  {key}: {value}")
```

## Requirements

### Space-Track.org Account
Most functions require a free account at https://space-track.org for TLE data access.

### Environment Variables
Set these in your shell or script:
```bash
export SPACETRACK_ACCT="your_email@domain.com"
export SPACETRACK_PASS="your_password"
```

### Dependencies
- pandas: Data manipulation and analysis
- numpy: Numerical computing
- matplotlib: Plotting and visualization
- pyephem: Astronomical calculations
- astropy: Time and coordinate transformations
- blimpy: HDF5 observation file handling
- requests: HTTP requests for API access

## Output Files

### CSV Files
- `files_affected_by_sats.csv`: Summary of all analyzed observations
- `{satellite}_{target}_separation.csv`: Detailed separation data for each satellite

### Plot Files
- `{target}_{satellites}_wf.png`: Waterfall plots of observations
- `{target}_{satellite}_separation.png`: Separation plots over time

### TLE Files
- `{month}_{day}_{year}_TLEs.txt`: Downloaded satellite orbital data

All output files are saved to the specified `work_dir` or current working directory if not specified.
