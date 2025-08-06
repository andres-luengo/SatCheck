"""
SatCheck - A package to look for satellites in Breakthrough Listen Data

This package provides functionality to search for satellite interference
in radio astronomy data from Breakthrough Listen. It analyzes HDF5 observation
files to detect potential satellite interference by comparing observation 
coordinates and times with satellite orbital data from Space-Track.org.

Main Features
-------------
- Automated satellite interference detection in radio astronomy data
- Integration with Space-Track.org for current satellite orbital data  
- Support for multiple observation file formats and input methods
- Visualization tools for separation analysis and waterfall plots
- Comprehensive output including CSV summaries and detailed plots

Key Functions
-------------
findSats : Main satellite detection function
plotSep : Generate satellite separation plots  
plotH5 : Generate observation waterfall plots
queryUCS : Download satellite database
query_space_track : Fetch TLE data from Space-Track.org

Requirements
------------
- Space-Track.org account for TLE data access
- Python 3.8+
- Dependencies: pandas, numpy, matplotlib, pyephem, astropy, blimpy

Basic Usage
-----------
>>> import satcheck
>>> results = satcheck.findSats(dir="/data/observations/")
>>> print(f"Analyzed {len(results)} files")

For detailed documentation of all functions, see FUNCTION_DOCUMENTATION.md
"""

from .findSats import findSats
from .genPlotsAll import plotSep, plotH5
from .findSatsHelper import (
    find_files,
    pull_relevant_header_info,
    convert,
    query_space_track,
    load_tle,
    separation,
    queryUCS,
    plotSeparation
)

__version__ = "0.1.0"
__all__ = [
    "findSats",
    "plotSep", 
    "plotH5",
    "find_files",
    "pull_relevant_header_info", 
    "convert",
    "query_space_track",
    "load_tle",
    "separation",
    "queryUCS",
    "plotSeparation"
]
