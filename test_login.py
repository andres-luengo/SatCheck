#!/usr/bin/env python3
"""
Simple script to test SpaceTrack login credentials
"""

import os
import requests

def test_spacetrack_login():
    """Test SpaceTrack authentication using environment variables"""
    
    # Get credentials from environment variables
    spacetrack_account = os.environ.get('SPACETRACK_ACCT')
    spacetrack_password = os.environ.get('SPACETRACK_PASS')
    
    # Check if credentials are available
    if not spacetrack_account or not spacetrack_password:
        print("❌ ERROR: SpaceTrack credentials not found in environment variables.")
        print("Please set SPACETRACK_ACCT and SPACETRACK_PASS environment variables.")
        return False
    
    print(f"Testing login for account: {spacetrack_account}")
    
    # Create session and attempt login
    session = requests.Session()
    login_data = {
        'identity': spacetrack_account,
        'password': spacetrack_password
    }
    
    try:
        # Attempt authentication
        login_response = session.post('https://www.space-track.org/ajaxauth/login', data=login_data)
        
        print(f"Login response status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            # Check response content for success/failure indicators
            response_text = login_response.text.lower()
            
            if 'failed' in response_text or 'login' in response_text:
                print("❌ FAILED: Authentication was rejected (wrong credentials)")
                return False
            else:
                print("✅ SUCCESS: Authentication successful!")
                
                # Test a simple query to confirm session works
                test_url = 'https://www.space-track.org/basicspacedata/query/class/tle_latest/NORAD_CAT_ID/25544/limit/1/format/3le'
                test_response = session.get(test_url)
                
                if test_response.status_code == 200 and len(test_response.text.strip()) > 0:
                    print("✅ SUCCESS: Test query returned data")
                    print(f"Sample TLE data: {test_response.text[:100]}...")
                else:
                    print("⚠️  WARNING: Login worked but test query failed")
                    print(f"Test query status: {test_response.status_code}")
                
                return True
        else:
            print(f"❌ FAILED: HTTP error {login_response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Network error - {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: Unexpected error - {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    print("SpaceTrack Login Test")
    print("=" * 30)
    
    success = test_spacetrack_login()
    
    print("=" * 30)
    if success:
        print("✅ Login test PASSED - your credentials are working!")
    else:
        print("❌ Login test FAILED - check your credentials or network connection")
