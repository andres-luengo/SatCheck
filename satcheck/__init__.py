"""
SatCheck - A package to look for satellites in Breakthrough Listen Data

This package provides functionality to search for satellite interference
in radio astronomy data from Breakthrough Listen.

Main modules:
- findSats: Main satellite search functionality
- findSatsHelper: Helper functions for satellite finding
- genPlotsAll: Plotting functions for visualization
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
