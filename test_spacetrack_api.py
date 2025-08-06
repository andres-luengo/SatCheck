#!/usr/bin/env python3
"""
Quick test script to debug SpaceTrack API issues
"""

import os
import tempfile
import requests

def test_spacetrack_authentication():
    """Test just the authentication part"""
    
    spacetrack_account = os.environ.get('SPACETRACK_ACCT')
    spacetrack_password = os.environ.get('SPACETRACK_PASS')
    
    if not spacetrack_account or not spacetrack_password:
        print("ERROR: Space-Track.org credentials not found in environment variables.")
        print("Set SPACETRACK_ACCT and SPACETRACK_PASS environment variables.")
        return False
    
    print(f"Testing authentication with username: {spacetrack_account}")
    
    # Create a session for proper authentication
    session = requests.Session()
    
    # Login data for authentication
    login_data = {
        'identity': spacetrack_account,
        'password': spacetrack_password
    }
    
    try:
        # First authenticate to get session cookies
        login_response = session.post('https://www.space-track.org/ajaxauth/login', data=login_data)
        
        print(f"Login response status: {login_response.status_code}")
        print(f"Login response text length: {len(login_response.text)}")
        
        if login_response.status_code == 200:
            # Check if login was actually successful
            if 'Failed' in login_response.text or 'Login' in login_response.text:
                print("FAILED: Authentication failed based on response content")
                return False
            else:
                print("SUCCESS: Authentication appears successful")
                
                # Test a simple query
                test_query = 'https://www.space-track.org/basicspacedata/query/class/tle_latest/NORAD_CAT_ID/25544/format/3le'
                print(f"Testing query: {test_query}")
                
                response = session.get(test_query)
                print(f"Test query response status: {response.status_code}")
                print(f"Test query response length: {len(response.text)}")
                
                if response.status_code == 200 and len(response.text.strip()) > 0:
                    print("SUCCESS: Test query returned data")
                    print(f"Sample response: {response.text[:200]}...")
                    return True
                else:
                    print("FAILED: Test query returned no data")
                    return False
        else:
            print(f"FAILED: Authentication failed with status code {login_response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR: Exception during testing: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    success = test_spacetrack_authentication()
    if success:
        print("\n✅ SpaceTrack authentication is working!")
    else:
        print("\n❌ SpaceTrack authentication failed.")
