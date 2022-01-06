'''
Modified from Chris Murphy's Satllite code
see: https://github.com/stevecroft/bl-interns/blob/master/chrismurphy/find_satellites.py
'''

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse

import ephem

from findSatsHelper import *

def main():
    '''
    dir [str] : directory that contains h5 files to check for satellites
                must end with a '/'
    '''

    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', help='Directory with h5 files to run on', default=False)
    args = parser.parse_args()

    months = {"01":"jan", "02":"feb","03":"mar","04":"apr","05":"may","06":"jun",
                  "07":"jul","08":"aug","09":"sep","10":"oct","11":"nov", "12":"dec"}


    df = pd.read_csv(queryUCS(), header=1)
    gps = np.where(df['Purpose'] == 'Navigation/Global Positioning')[0]
    gps_data = df.loc[gps]
    gps_id_list = gps_data['NORAD Number'].tolist()
    print(len(gps_id_list))

    gps_list = []
    gps_ids = ''
    for i in gps_id_list:
        gps_ids = gps_ids + str(i) + ','

    list_of_filenames = find_files(args.dir)

    start_time_mjd, right_ascension, declination = pull_relevant_header_info(list_of_filenames)

    year_month_day_time = convert_mjd_to_date(start_time_mjd)

    tles = query_space_track(list_of_filenames, gps_ids)
    print(tles)

    gbt = ephem.Observer()
    gbt.long = "-79.839857"
    gbt.lat = "38.432987"
    gbt.elevation = 807.0


    ra_lst = []
    dec_lst = []
    for z in list_of_filenames:
        ra = pull_ra(z)
        dec = pull_dec(z)
        ra_lst.append(ra)
        dec_lst.append(dec)

    files_affected_by_sats = {}
    for (fil_file, ra, dec, date) in zip(list_of_filenames, ra_lst, dec_lst, year_month_day_time):
        mjd = pull_start_time(fil_file)
        date = convert(mjd)
        year = date.split("-")[0]
        mon = date.split("-")[1]
        day1 = date.split("-")[2].split('T')[0]
        filename = months[mon] + '_' + day1 + "_" +year + "_TLEs.txt"

        print(fil_file + " matches with " + filename)
        fig, ax = plt.subplots()
        for tle in tles:
            if filename == tle:
                satdict = load_tle(tle)
                sat_hit_dict = separation(satdict, ra, dec, date, gbt)

                print(sat_hit_dict)
                print("\n\n")

                if len(sat_hit_dict.keys()) > 0:


                    for stored_sats_in_obs, unique_sat_info in sat_hit_dict.items():

                        print("++++++++++++++++++")

                        plt.scatter(unique_sat_info['Time after start'], unique_sat_info['Separation'], s = 1, label = stored_sats_in_obs)
                        minpoint = min(unique_sat_info['Separation'])

                        minindex = unique_sat_info['Separation'].index(minpoint)
                        mintime = unique_sat_info['Time after start'][minindex]
                        print("++++++++++++++++++++++")
                        print(minindex , mintime , minpoint)
                        print("++++++++++++++++++++++++")
                        print("++++++++++++++++++++++++\n\n")
                        #plt.hlines(y=minpoint, xmin = 1, xmax = 300, label = 'Minpoint: ' + str(minpoint))
                        #plt.hlines(unique_sat_info['Time after start'], unique_sat_info['Separation'], lw = 2, label = minpoint)
                        plt.scatter(mintime, minpoint, s = 10, label = 'Min: ' + str("%.5fdeg " % minpoint) + str(mintime) + "s")
                        ymax = ephem.degrees('03:00:00')
                        ymax_rad = repr(ymax)

                        ymax_deg = np.rad2deg(float(ymax_rad))

                        plt.xlabel('Time after start (seconds)')
                        plt.ylabel('Separation (degrees)')
                        plt.xlim(0, 300)
                        plt.ylim(0, ymax_deg)
                        plot_name = fil_file.split('_')[-2] + '_' + fil_file.split('_')[-1]
                        plt.title(plot_name)
                        plt.legend()
                        plt.savefig(plot_name + '_time_sep_.png')
                        files_affected_by_sats[fil_file] = minpoint

    print(files_affected_by_sats)


if __name__ == '__main__':
    sys.exit(main())
