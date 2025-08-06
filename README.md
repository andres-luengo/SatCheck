# SatCheck

Repo with some code to look for satellites in Breakthrough Listen Data. Modified from: https://github.com/stevecroft/bl-interns/blob/master/chrismurphy/find_satellites.py

## Installation

To install this package for use in other projects:

```bash
pip install .
```

Or for development:

```bash
pip install -e .
```

## Package Usage

After installation, you can use satcheck in your Python projects:

```python
import satcheck

# Use the main satellite finding function
affected_files = satcheck.findSats(
    dir="/path/to/h5/files/",
    file=None,
    pattern="*.h5", 
    plot=False,
    n=10
)

# Use helper functions
h5_files = satcheck.find_files("/path/to/h5/files/", None, "*.h5")
start_times, ra_list, dec_list = satcheck.pull_relevant_header_info(h5_files)

# Use plotting functions
satcheck.plotSep("path/to/separation.csv")
satcheck.plotH5(["satellite_csv1.csv"], "observation.h5")
```

## Command Line Usage

After installation, you can also use the command-line tools:

### `findSats` Usage
You must add the username and password for spacetrack queries to your .bashrc file using the following steps in a bash terminal
```
sudo nano ~/.bashrc
```
Then add to the bottom the line
```
export SPACETRACK_ACCT="{Username}"
export SPACETRACK_PASS="{Password}"
```
where you replace {Username} with your username (your email, by default) and {Password} with your password. Then exit nano and type
```
source ~/.bashrc
```

### Setup for Space Track queries
`findSats` is a program that allows the user to search for satellites that cross
the observation. It checks across date/time and sky location but does not check
frequency since the downlink frequency of most satellites is unknown. This means
that visual inspection of the hdf5 files and corresponding satellite passes is
required to confirm the existence of a satellite in the data. See the section on
`genPlotsAll` for helpful plotting code.

To use `findSats` in the command line there are a few different options:

* dir -> the directory with the hdf5 file(s) to search for satellites in
* file -> a text file with a list of hdf5 files to to search on
* pattern -> If an input directory is used, this pattern will be used in glob to limit files to run on. An example would be if you only wanted files ending in 0000.h5 you could input `*0000.h5`. The default is simply all h5 files (*.h5).
* plot -> Boolean (True or False). If True plots of the separation will be generated. Default is set to False. This just implements a function in the genPlotsAll code.
* n -> Do not change this input value unless you know what you're doing!! This changes the number of partitions of the list with NORAD numbers and affects the query speed of Space Track. The default is set to 10 and should not be set any lower.

Note that either a directory of h5 files (`dir`) should be provided or a file with a list of h5 files (`file`). An example call would be
```
python3 ~/SatCheck/genPlotsAll.py --file list_of_cadences.txt
```

## `genPlotsAll.py` Usage
`genPlotsAll` generates both a waterfall plot of the h5 files and all of the corresponding satellite pass plots (time vs. separation). Here is the command line options of genPlotsAll:

* h5Dir -> the directory with hdf5 files to run on. This is an optional argument as long as genPlotsAll is being run in the same directory as the `files_affected_by_sats.csv` file outputted by `find_sats`.
* memLim -> the memory limit to implement when creating the h5 waterfall plots. Default is 40 GB, may need to be raised for larger X band files.

Example usage when running in same directory as the files_affected_by_sats.csv file:
```
python3 ~/SatCheck/genPlotsAll.py
```

Example usage when there is a separate directory of h5 files:
```
python3 ~/SatCheck/genPlotsAll.py --h5Dir path/to/h5Dir
```
