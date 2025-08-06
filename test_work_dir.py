#!/usr/bin/env python3
"""
Simple test to verify work_dir parameter functionality
"""

import os
import tempfile
import shutil
from satcheck.findSatsHelper import queryUCS

def test_work_dir():
    """Test that work_dir parameter works correctly"""
    
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp(prefix="satcheck_test_")
    print(f"Testing with work_dir: {temp_dir}")
    
    try:
        # Test queryUCS with custom work_dir
        print("Testing queryUCS with custom work_dir...")
        ucs_file = queryUCS(work_dir=temp_dir)
        
        # Verify file was created in the correct location
        expected_path = os.path.join(temp_dir, 'UCS-Satellite-Database.txt')
        if os.path.exists(expected_path):
            print(f"✓ UCS database correctly saved to: {expected_path}")
            print(f"✓ File size: {os.path.getsize(expected_path)} bytes")
        else:
            print(f"✗ UCS database not found at expected location: {expected_path}")
            
        # Test queryUCS with default (current directory)
        print("\nTesting queryUCS with default work_dir...")
        ucs_file_default = queryUCS()
        default_expected = os.path.join(os.getcwd(), 'UCS-Satellite-Database.txt')
        
        if os.path.exists(default_expected):
            print(f"✓ UCS database correctly saved to default location: {default_expected}")
        else:
            print(f"✗ UCS database not found at default location: {default_expected}")
            
    except Exception as e:
        print(f"✗ Error during test: {e}")
    
    finally:
        # Clean up
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"✓ Cleaned up temporary directory: {temp_dir}")
            
        # Clean up default file if it exists
        default_file = os.path.join(os.getcwd(), 'UCS-Satellite-Database.txt')
        if os.path.exists(default_file):
            os.remove(default_file)
            print(f"✓ Cleaned up default file: {default_file}")

if __name__ == "__main__":
    test_work_dir()
    print("Test completed!")
