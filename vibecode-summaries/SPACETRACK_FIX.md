# Space-Track.org API Fix

## Problem
The SatCheck package was experiencing a "ValueError: line does not conform to tle format" error when trying to download satellite TLE (Two-Line Element) data from Space-Track.org. The downloaded TLE files contained the error message "Single command deprecated. See API help for cookie use." instead of actual satellite data.

## Root Cause
Space-Track.org updated their API and deprecated the old single-command authentication method. The old code was attempting to authenticate and query data in a single POST request, which is no longer supported.

## Solution
Updated the `query_space_track()` function in `satcheck/findSatsHelper.py` to use proper session-based authentication:

### Key Changes:

1. **Session-based Authentication**: 
   - Create a `requests.Session()` object
   - First authenticate with Space-Track.org using POST to `/ajaxauth/login`
   - Use the authenticated session to make the actual data query with GET

2. **Better Error Handling**:
   - Check response status codes
   - Validate that the response contains actual TLE data, not error messages
   - Skip files that contain deprecated API messages
   - Provide informative error messages

3. **Improved TLE File Loading**:
   - Enhanced `load_tle()` function to handle invalid or empty TLE files
   - Skip malformed TLE entries instead of crashing
   - Detect and warn about files containing error messages instead of TLE data

4. **Checkpoint File Update**:
   - Updated the outdated checkpoint file to prevent accidental usage of old code

## Files Modified:
- `satcheck/findSatsHelper.py` - Main fix for Space-Track.org API
- `.ipynb_checkpoints/findSatsHelper-checkpoint.py` - Added deprecation notice
- `test_spacetrack_fix.py` - New test script to verify the fix

## Testing
The fix has been tested for:
- ✅ Syntax correctness
- ✅ Import functionality
- ⚠️  Live API calls (requires Space-Track.org credentials)

## Usage
The fix is backward compatible. The same function calls will work, but now they'll use the updated API method:

```python
import satcheck

# This will now use the fixed Space-Track.org API
affected_files = satcheck.findSats(
    file_list=[some_path],
    spacetrack_account=spacetrack_account,
    spacetrack_password=spacetrack_password
)
```

## Credentials Required
Users still need to set up their Space-Track.org credentials as environment variables:
```bash
export SPACETRACK_ACCT="your_email@example.com"
export SPACETRACK_PASS="your_password"
```

The fix should resolve the "Single command deprecated" error and allow proper downloading of satellite TLE data from Space-Track.org.
