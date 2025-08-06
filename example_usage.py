#!/usr/bin/env python3
"""
Example usage of the satcheck package

This example shows how to use the main functions from satcheck
in a separate Python project after installation.
"""

import satcheck
import pandas as pd
import numpy as np

def example_usage():
    """
    Example of how to use satcheck in your own project
    """
    
    # Example 1: Use helper functions
    print("SatCheck version:", satcheck.__version__)
    print("Available functions:", satcheck.__all__)
    
    # Example 2: Query UCS Database with custom work directory
    import tempfile
    temp_dir = tempfile.mkdtemp(prefix="satcheck_output_")
    ucs_file = satcheck.queryUCS(work_dir=temp_dir)
    print(f"Downloaded UCS database to: {ucs_file}")
    
    # Or use default current directory
    # ucs_file = satcheck.queryUCS()
    # print(f"Downloaded UCS database to: {ucs_file}")
    
    # Example 3: Find files matching a pattern
    # If you had h5 files in a directory:
    # h5_files = satcheck.find_files("/path/to/h5/files/", None, "*.h5")
    # print(f"Found {len(h5_files)} h5 files")
    
    # Example 4: Use the main findSats function with custom work directory
    # This would be used with actual h5 files and would require proper setup
    # affected_files = satcheck.findSats(
    #     dir="/path/to/h5/files/",
    #     file=None,
    #     pattern="*.h5",
    #     plot=False,
    #     n=10,
    #     work_dir="/path/to/output/directory"  # Specify where to store output files
    # )
    
    # Or use default current directory:
    # affected_files = satcheck.findSats(
    #     dir="/path/to/h5/files/",
    #     file=None,
    #     pattern="*.h5",
    #     plot=False,
    #     n=10
    # )
    
    print("Example completed!")

if __name__ == "__main__":
    example_usage()
