#!/usr/bin/env python3
"""
Test script to verify that the main fixes work with a small test case
"""

import os
import tempfile
import satcheck
from satcheck.findSatsHelper import queryUCS
import pandas as pd

def test_satcheck_fixes():
    """Test the fixed functionality with minimal data"""
    
    spacetrack_account = os.environ.get('SPACETRACK_ACCT')
    spacetrack_password = os.environ.get('SPACETRACK_PASS')
    
    if not spacetrack_account or not spacetrack_password:
        print("ERROR: Space-Track.org credentials not found in environment variables.")
        return False
    
    print("Testing SatCheck fixes...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temporary directory: {temp_dir}")
        
        # Test the UCS database query first
        try:
            print("Testing UCS database query...")
            ucs_file = queryUCS(work_dir=temp_dir)
            print(f"UCS database downloaded to: {ucs_file}")
            
            # Check the database content
            df = pd.read_csv(ucs_file)
            print(f"Total satellites in UCS database: {len(df)}")
            print(f"Columns: {list(df.columns)[:10]}...")  # Show first 10 columns
            
            if 'NORAD Number' in df.columns:
                valid_norad = df[df['NORAD Number'] > 0]
                print(f"Satellites with valid NORAD numbers: {len(valid_norad)}")
                print(f"Sample NORAD numbers: {valid_norad['NORAD Number'].head().tolist()}")
            
            return True
            
        except Exception as e:
            print(f"ERROR during UCS database test: {e}")
            return False

if __name__ == "__main__":
    success = test_satcheck_fixes()
    if success:
        print("\n✅ Basic SatCheck functionality tests passed!")
        print("   The UCS database query is working correctly.")
        print("   You can now try running your full satcheck.findSats() call.")
    else:
        print("\n❌ There are still issues with the basic functionality.")
