#!/usr/bin/env python3
"""
Debug script to check filename matching issue
"""

import os
import tempfile
import numpy as np

def test_filename_matching():
    """Test filename matching logic"""
    
    # Example data similar to what your code would have
    work_dir = "/tmp/test_satcheck"
    os.makedirs(work_dir, exist_ok=True)
    
    # Simulate what downloadTLEs returns (full paths)
    tles = np.array([
        "/tmp/test_satcheck/jun_21_2020_TLEs.txt",
        "/tmp/test_satcheck/jun_22_2020_TLEs.txt",
        "/tmp/test_satcheck/jul_15_2020_TLEs.txt"
    ])
    
    # Create test files
    for tle_file in tles:
        with open(tle_file, 'w') as f:
            f.write("0 TEST SAT\n1 12345U ...\n2 12345 ...\n")
    
    # Test the filename matching logic
    months = {"01":"jan", "02":"feb","03":"mar","04":"apr","05":"may","06":"jun",
              "07":"jul","08":"aug","09":"sep","10":"oct","11":"nov", "12":"dec"}
    
    # Test case 1: Should find match
    date = "2020-06-21T10:30:45.123456"
    year = date.split("-")[0]
    mon = date.split("-")[1]
    day1 = date.split("-")[2].split('T')[0]
    filename = months[mon] + '_' + day1 + "_" + year + "_TLEs.txt"
    full_filename = os.path.join(work_dir, filename)
    
    print(f"Looking for: {filename}")
    print(f"Full path: {full_filename}")
    print(f"Available TLE files:")
    for t in tles:
        print(f"  {t}")
    
    whichTLE = np.where(full_filename == tles)[0]
    print(f"Match found: {len(whichTLE) > 0}")
    print(f"whichTLE array: {whichTLE}")
    
    if len(whichTLE) > 0:
        print(f"Would use file: {tles[whichTLE][0]}")
    else:
        print("No match found - this would cause the IndexError!")
    
    # Clean up
    for tle_file in tles:
        if os.path.exists(tle_file):
            os.remove(tle_file)
    os.rmdir(work_dir)

if __name__ == "__main__":
    test_filename_matching()
