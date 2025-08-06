# SatCheck Quick Reference

## Installation

```bash
pip install .  # or pip install -e . for development
```

## Setup Space-Track.org Credentials

```bash
export SPACETRACK_ACCT="your_email@domain.com"  
export SPACETRACK_PASS="your_password"
```

## Most Common Usage Patterns

### 1. Basic Satellite Detection

```python
import satcheck

# Analyze all HDF5 files in a directory
results = satcheck.findSats(dir="/path/to/observations/")

# Check which files have satellite interference
affected = results[results['satellite?'] == True]
print(f"Found satellites in {len(affected)} files")
```

### 2. Analyze Specific Files

```python
# From a text file listing observation paths
results = satcheck.findSats(file="observation_list.txt")

# From a Python list
file_list = ["obs1.h5", "obs2.h5", "obs3.h5"]
results = satcheck.findSats(file_list=file_list)
```

### 3. Generate Plots

```python
# Include plots during analysis
results = satcheck.findSats(dir="/data/obs/", plot=True)

# Or generate plots separately
satcheck.plotSep("satellite_separation.csv")
satcheck.plotH5(["sat1.csv", "sat2.csv"], "observation.h5")
```

### 4. Specify Output Directory

```python
# Store all outputs in specific directory
results = satcheck.findSats(
    dir="/data/observations/",
    work_dir="/analysis/satellite_check/",
    plot=True
)
```

## Command Line Usage

```bash
# Analyze directory of observations
findSats --dir /data/obs/ --work_dir /output/ --plot True

# Analyze files from list
findSats --file observation_list.txt --work_dir /output/

# Generate plots after analysis
genPlotsAll --work_dir /output/
```

## Output Files

- `files_affected_by_sats.csv` - Summary of all observations
- `{satellite}_{target}_separation.csv` - Detailed separation data
- `{target}_{satellites}_wf.png` - Waterfall plots  
- `{target}_{satellite}_separation.png` - Separation plots

## Key Parameters

- `dir`: Directory containing HDF5 files
- `file`: Text file with list of HDF5 paths
- `file_list`: Python list of HDF5 paths
- `pattern`: Glob pattern (default: "*.h5")
- `plot`: Generate plots (default: False)
- `work_dir`: Output directory (default: current directory)
- `n`: Satellite query partitions (default: 10, don't change)

## Results DataFrame Columns

- `filepath`: Path to observation file
- `satellite?`: True if satellites detected
- `minSeparation`: Closest approach distances (degrees)  
- `minTime`: Times of closest approaches (seconds)
- `csvPaths`: Paths to detailed separation files

## Troubleshooting

**Authentication Errors**: Check Space-Track.org credentials
**No TLE Data**: Historical data may not exist for requested dates
**Memory Errors**: Increase `memLim` parameter for large files
**Missing Files**: Verify HDF5 file paths and permissions
