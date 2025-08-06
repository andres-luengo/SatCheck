#!/usr/bin/env python3
"""
Test script to check specific satellite IDs and date ranges
"""

import os
import requests

def test_historical_query():
    """Test querying for historical TLE data from June 2020"""
    
    spacetrack_account = os.environ.get('SPACETRACK_ACCT')
    spacetrack_password = os.environ.get('SPACETRACK_PASS')
    
    if not spacetrack_account or not spacetrack_password:
        print("ERROR: Space-Track.org credentials not found")
        return False
    
    session = requests.Session()
    login_data = {
        'identity': spacetrack_account,
        'password': spacetrack_password
    }
    
    try:
        # Authenticate
        login_response = session.post('https://www.space-track.org/ajaxauth/login', data=login_data)
        
        if login_response.status_code != 200:
            print(f"Authentication failed: {login_response.status_code}")
            return False
        
        # Test with GPS satellites (known to exist) for June 2020
        gps_satellites = ["28361", "28474", "28897", "29486", "29601"]  # Some GPS satellites
        test_ids = ",".join(gps_satellites)
        
        # Historical date range - June 21, 2020
        date1 = "2020-06-21"
        date2 = "2020-06-22"
        
        print(f"Testing with satellite IDs: {test_ids}")
        print(f"Date range: {date1} to {date2}")
        
        # Try the historical query
        query_url = f'https://www.space-track.org/basicspacedata/query/class/tle/EPOCH/{date1}--{date2}/NORAD_CAT_ID/{test_ids}/orderby/TLE_LINE1 ASC/format/3le'
        print(f"Query URL: {query_url}")
        
        response = session.get(query_url)
        print(f"Response status: {response.status_code}")
        print(f"Response length: {len(response.text)}")
        
        if response.status_code == 200:
            if len(response.text.strip()) > 0:
                print("SUCCESS: Historical data found")
                print(f"Sample response: {response.text[:200]}...")
                return True
            else:
                print("No historical data found for these satellites/dates")
                
                # Try a broader date range
                print("Trying broader date range...")
                broad_date1 = "2020-06-01"
                broad_date2 = "2020-06-30"
                
                broad_query_url = f'https://www.space-track.org/basicspacedata/query/class/tle/EPOCH/{broad_date1}--{broad_date2}/NORAD_CAT_ID/{test_ids}/orderby/TLE_LINE1 ASC/format/3le'
                broad_response = session.get(broad_query_url)
                
                print(f"Broad query response status: {broad_response.status_code}")
                print(f"Broad query response length: {len(broad_response.text)}")
                
                if len(broad_response.text.strip()) > 0:
                    print("SUCCESS: Broad date range found data")
                    return True
                else:
                    print("No data found even with broad date range")
                    
                    # Try latest data instead
                    print("Trying latest TLE data for these satellites...")
                    latest_query_url = f'https://www.space-track.org/basicspacedata/query/class/tle_latest/NORAD_CAT_ID/{test_ids}/format/3le'
                    latest_response = session.get(latest_query_url)
                    
                    if latest_response.status_code == 200 and len(latest_response.text.strip()) > 0:
                        print("SUCCESS: Latest TLE data found")
                        print(f"Sample response: {latest_response.text[:200]}...")
                        return True
                    else:
                        print("No TLE data found for these satellite IDs at all")
                        return False
        else:
            print(f"Query failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    test_historical_query()
