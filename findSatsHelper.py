import os, sys, time, glob
import math
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from blimpy import Waterfall
from astropy.time import Time , TimeDelta
from datetime import datetime, date, timedelta
import ephem
from astropy import units as u
from astropy.coordinates import SkyCoord, EarthLocation, AltAz #,Angle
import requests
import urllib
from io import StringIO

'''
Following 10 functions taken from Chris Murphy's satellite code

see: https://github.com/stevecroft/bl-interns/blob/master/chrismurphy/find_satellites.py
'''

def find_files(inDir):

    #file = open('thresholded_significant_hits.txt')
    #content = file.read().split("\n")
    #file.close()
    #return content[:-1]

    # read from input directory
    return glob.glob(inDir+'*.h5')



def pull_relevant_header_info(filename_array):

    start_time_mjd_array =[]
    right_ascension_array = []
    declination_array = []

    for every_file in filename_array:

        wf = Waterfall(every_file, load_data=False)

        start_time_mjd = wf.header['tstart']
        right_ascension = wf.header['src_raj']
        declination = wf.header['src_dej']

        start_time_mjd_array.append(start_time_mjd)
        right_ascension_array.append(right_ascension)
        declination_array.append(declination)

    return start_time_mjd_array, right_ascension_array, declination_array

def pull_ra(file):
    wf = Waterfall(file, load_data=False)
    right_ascension = str(wf.header['src_raj'])
    #right_ascension = right_ascension.degree
    return right_ascension

def pull_dec(file):
    wf = Waterfall(file, load_data=False)
    declination = str(wf.header['src_dej'])
    #declination = declination.degree
    return declination

def pull_start_time(file):
    wf = Waterfall(file, load_data=False)
    start_time_mjd = wf.header['tstart']
    return start_time_mjd


def convert_mjd_to_date(start_time_mjd):

    array_of_start_times = []
    startdate = Time(start_time_mjd, format='mjd') # Beginning mjd of observation
    string_start_date = Time(startdate, format='isot')

    for x in string_start_date:
        array_of_start_times.append(str(x))

    return array_of_start_times

def convert(mjd):
    startdate = Time(mjd, format='mjd')
    print(startdate)
    string_start_date = str(Time(startdate, format='isot'))
    print(string_start_date)
    return string_start_date

def query_space_track(fil_files, gps_ids, overwrite=False):

    print("Querying Space Track...")
    monthConversion = {"01":"jan", "02":"feb","03":"mar","04":"apr","05":"may","06":"jun",
                  "07":"jul","08":"aug","09":"sep","10":"oct","11":"nov", "12":"dec"}

    array_of_TLE_filenames = []
    for files in fil_files:
        wf = Waterfall(files, load_data=False)
        start_time_mjd = wf.header['tstart']
        mjd = Time(start_time_mjd, format='mjd')
        time_isot = Time(mjd, format='isot')
        day_change = TimeDelta(1 , format = 'jd')
        time_mjd_change = mjd + day_change
        time_isot_change = Time(time_mjd_change , format = 'isot')
        str_time1 = str(time_isot)
        str_time2 = str(time_isot_change)

        year_full_1 = str_time1.split("-")[0]
        year_full_2 = str_time2.split("-")[0]

        mon1 = str_time1.split("-")[1]
        day1 = str_time1.split("-")[2].split('T')[0]

        mon2 = str_time2.split("-")[1]
        day2 = str_time2.split("-")[2].split('T')[0]

        filename = monthConversion[mon1] + "_" + day1 + '_' + year_full_1 + "_TLEs.txt"

        if not os.path.isfile(filename) or overwrite:

            print('######################################################################')
            print("Downloading active GPS satellite TLEs from Space-Track: " , filename)
            print('######################################################################')
            #array_of_TLE_filenames.append(filename)
            #Query space track for properly dated TLE info
            date1 = year_full_1+'-'+mon1+'-'+day1
            date2 = year_full_2+'-'+mon1+'-'+day2

            #MEO parameters: Eccentricity < .25 . 600 < Period < 800
            #Ascending epoch. Dictionary will append most recent epoch
            #Using only active sats
            data = [
            ('identity', 'noahfranz13junk@gmail.com'),
            ('password', 'HelloNoah12345!'),
            ('query', 'https://www.space-track.org/basicspacedata/query/class/tle/EPOCH/'+date1+'--'+date2+'/NORAD_CAT_ID/'+gps_ids+'/orderby/TLE_LINE1 ASC/format/3le'),
            ]

            response = requests.post('https://www.space-track.org/ajaxauth/login', data=data)

            with open(filename, 'w+') as file:
                file.write(response.content.decode())

            time.sleep(3)

        if filename not in array_of_TLE_filenames:
            array_of_TLE_filenames.append(filename)

    return array_of_TLE_filenames


def load_tle(filename):
    #Loads a TLE file and creates a list of satellites
    '''
    Space Track is coming back with multiple TLEs for one satellite, with slightly different epochs
    Even when we download a TLE for that day, it comes back with two/three slightly different info
    Order satellites with ascending epoch, that way the last one we append to the dictionary
    has the most recent epoch and TLE info
    '''
    f = open(filename)
    satlist = []
    satdict = {}
    l1 = f.readline()
    while l1:
        l2 = f.readline()
        l3 = f.readline()
        sat = ephem.readtle(l1,l2,l3)
        name = sat.name

        identity = l3.split(' ')[1]
        #epoch = l2.split(' ')[5].split('.')[1]
        real_sat = name.replace('0 ', '') + ' ' + identity
        satdict[real_sat] = sat
        satlist.append(sat)
        l1 = f.readline()

    f.close()


    print("%i TLEs loaded into: "%len(satlist) , filename)
    print("%i unique satellites loaded: "%len(satdict.keys()))
    return satdict


def separation(tle, ra_obs, dec_obs, start_time, gbt):
    sat_hit_dict = {}
    ra_obs = ra_obs.replace('h', ':').replace('m', ':').replace('s', '')
    print("ra_obs  [", type(ra_obs).__name__, "]   :", ra_obs)
    dec_obs = dec_obs.replace('d', ':').replace('m',':').replace('s','')
    print("dec_obs  [", type(dec_obs).__name__, "]   :", dec_obs)

    dec_obs = ephem.degrees(dec_obs)
    print("dec_obs  [", type(dec_obs).__name__, "]   :", dec_obs)
    ra_obs = ephem.hours(ra_obs)
    print("ra_obs  [", type(ra_obs).__name__, "]   :", ra_obs)

    for unique_sats, satellite_object in tle.items():
        ra = []
        dec = []
        close_sats = []
        close_sep = []
        close_time = []
        time_after = []
        unique_sat_name = {}
        time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%f")
        time_after_start = 0
        for delta_time in range(0,300):
            time += timedelta(seconds = 1)
            time_after_start += 1
            gbt.date = time
            satellite_object.compute(gbt)
            sat_ra, sat_dec = str(satellite_object.ra) , str(satellite_object.dec)

            sep = ephem.separation((satellite_object.ra, satellite_object.dec), (ra_obs , dec_obs))

            sep_rad = repr(sep)

            sep_deg = np.rad2deg(float(sep_rad))

            if sep_deg < 3:

                ra.append(sat_ra)
                dec.append(sat_dec)
                close_sep.append(sep_deg)
                close_time.append(time)
                time_after.append(time_after_start)
                unique_sat_name['RA'] = ra
                unique_sat_name['DEC'] = dec
                unique_sat_name['Separation'] = close_sep
                unique_sat_name['Time after start'] = time_after
                sat_hit_dict[unique_sats] = unique_sat_name
                if satellite_object not in close_sats:
                    close_sats.append(satellite_object)

    return sat_hit_dict


'''
Now the rest of these functions I wrote
'''

def queryUCS():
    '''
    Queries the UCS Satellite Database and downloads the most up to date file info

    returns : path to the downloaded file
    '''

    url = 'https://www.ucsusa.org/sites/default/files/2021-11/UCS-Satellite-Database-9-1-2021.txt'
    outPath = os.path.join(os.getcwd(), 'UCS-Satellite-Database.txt')

    req = urllib.request.Request(url, headers={'User-Agent' : 'Mozilla/5.0'})
    ucsData = urllib.request.urlopen(req).read()

    strUCS = ucsData.decode('cp1252')
    dataArr = [s.split('\t') for s in strUCS.split('\n')]
    parsedData = pd.DataFrame(dataArr[1:], columns=dataArr[0])

    parsedData.to_csv()

    return outPath
