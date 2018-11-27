# coding: utf-8

# Script to update g values in FG-5/A-10 .project.txt files with laser drift and(or) a soil moisture correction.
# 
# The script works on project.txt files in a specified directory (and subdirectories). The g value in each
# .project.txt file is updated, and a comment added that describes the magnitude of the correction. The original
# .project.txt file is copied to a new file, where 'project.txt' in the filename is replaced with 'original.txt'.
# 
# Laser drift corrections are taken from an Excel workbook, specified as a parameter in the script.
# 
# Soil moisture corrections are taken from a text file downloaded from the
# ORNL DAAC. 2017. Soil Moisture Visualizer. ORNL DAAC, Oak Ridge, Tennessee, USA.
# http://dx.doi.org/10.3334/ORNLDAAC/1366
# 
# This service provides SMAP root zone soil moisture for a point location, from March 2015 onward. SMAP data
# represent the mean value of a 9 x 9km grid; all points within a cell have the same soil moisture time series.
# 
# A csv-file summary of the corrections is written, with the filename "Corrections_YYYY-MM-DD.csv"
# 
# Written for Python 2.7, updated for compatibility with Python 3.5 in 2018
# 
# Jeff Kennedy
# USGS
# 
# Updated 11/2/2018: Tkinter now tkinter, specify filedialog as import (lines 38-39). Updated line 61 to current tkinter syntax. 
# Added lines 98-100 to check for previous correction (existing 'original.txt' file) and break loop if found.
# Changed line 101 from <if string.find(fname, 'project.txt') != -1:> to <elif fname.find('project.txt') != -1:>
# Tested on partial copy of TAMA directory on 11/2/2018. Test successful.
# Tested on a directory with some files updated and some not - by the timestamp of files 
# it only applied the correction to previously uncorrected project.txt files.
# 

import string
import os
from tkinter import filedialog
from tkinter import *
import datetime
import pandas as pd
from time import strftime
import fnmatch


# User-specified options
update_laser = True
laser_cal_file = "\\\\Igswztwwgszona\\Gravity Data Archive\\Absolute Data\\A-10\\Instrument Maintenance\\Calibrations\\A10-008 clock and laser calibrations.xlsx"
laser_cal_worksheet = "DRIFT LOOKUP TABLE"

update_SM = False
if update_SM:
    sm_file = "BCnw_daily-smap-ORNL-DAAC-1s19jW.txt"
write_corrections_to_file = True

# Either use a specified directory, or show a GUI for the user to decide
pwd = os.getcwd()
root = Tk()
root.withdraw()
data_directory = filedialog.askdirectory(
    parent=root,initialdir=pwd)
#data_directory = u'\\\\Igswztwwgszona\\Gravity Data Archive\\Absolute Data\\A-10\\Final Data\\Big Chino\\PRESCOTT CB\\'

laser_corr, drift_rate, elapsed_days = -999, -999, -999
sm_at_time_of_g, sm, sm_corr = -999, -999, -999

if update_laser:
    xl = pd.ExcelFile(laser_cal_file)
    df_drift = xl.parse(laser_cal_worksheet)

if update_SM:
    df_sm = pd.read_csv(sm_file, header=4)
    sm_date = df_sm["time"]
    sm = df_sm["SMAP_rootzone"]
else:
    sm_corr = -999
    sm_at_time_of_g
    sm = pd.DataFrame([-999])

if write_corrections_to_file:
    # File save name is directory plus time and date
    fid = open('.\working_dir\Corrections_' + strftime("%Y%m%d-%H%M") + '.csv', 'w')
    fid.write('Station,Date,Drift_corr,Drift_rate,Elapsed_days_since_cal,SM_corr,SM,SM_mean\n')

# For each file in the data_directory and subdirectories
for dirname, dirnames, filenames in os.walk(data_directory):
    for filename in filenames:
        fname = os.path.join(dirname, filename)
        # If the file name ends in "project.txt"
        if fname.find('.original.txt') != -1:
            print('Already performed laser update')
            break
        elif fname.find('project.txt') != -1:
            #if fname.find('project.txt') != -1:
                os.system('cp "' + fname + '" "' + fname.replace('project.txt','.original.txt') + '"')
                print(fname)
                with open('temp.txt', "w") as fout:
                    correct_for_laser_drift = False  # set to true if valid correction is found
                    correct_for_sm = False           # set to true if valid correction is found
                    with open(fname) as project_file:
                        for line in project_file:
                            line_elements = line.split(" ")
                            # To deal with station names with spaces
                            if line_elements[0] == "Name:":
                                try:
                                    name = ''
                                    name += line_elements[1].strip()
                                    if len(line_elements) > 2:
                                        for idx, item in enumerate(line_elements):
                                            if idx > 1:
                                                name += '_'
                                                name += item.strip()
                                except:
                                    name = 'NAME_ERROR'
                                station = name
                            if line_elements[0] == "Date:":
                                date_str = line_elements[-1]
                                dt = datetime.datetime.strptime(date_str.strip(), "%m/%d/%y")
                            if line_elements[0] == "Gravity:":
                                if update_laser:
                                    for idx, row in df_drift.iterrows():
                                        if dt > row["BEGIN"]:
                                            if dt < row["END"]:
                                                drift_rate = row["MPD"]
                                                correct_for_laser_drift = True
                                                elapsed_days = dt - row["BEGIN"].to_pydatetime()
                                                elapsed_days = float(elapsed_days.days)
                                                laser_corr = elapsed_days * drift_rate
                                                break
                                if update_SM:
                                    for idx, row in df_sm.iterrows():
                                        if dt >= datetime.datetime.strptime(row.time, "%Y-%m-%d"):
                                            try:
                                                if dt < datetime.datetime.strptime(df_sm.loc[idx+1, "time"],"%Y-%m-%d"):
                                                    sm_at_time_of_g = row["SMAP_rootzone"]
                                                    correct_for_sm = True
                                                    sm_diff = sm_at_time_of_g - sm.mean()
                                                    sm_corr = sm_diff*0.42
                                                    break
                                            except:
                                                # at end of dataframe
                                                continue
                                g = float(line_elements[-2])
                                microGal_symbol = line_elements[-1]
                                if correct_for_laser_drift and correct_for_sm:
                                    corr_g = g - laser_corr - sm_corr
                                    fout.write('Gravity: ' + '{:9.2f}'.format(corr_g) + ' '
                                               + microGal_symbol)
                                elif correct_for_laser_drift:
                                    corr_g = g - laser_corr
                                    fout.write('Gravity: ' + '{:9.2f}'.format(corr_g) + ' '
                                               + microGal_symbol)
                                elif correct_for_sm:
                                    corr_g = g - sm_corr
                                    fout.write('Gravity: ' + '{:9.2f}'.format(corr_g) + ' '
                                               + microGal_symbol)
                                else:
                                    fout.write(line)
                            else:
                                fout.write(line)

                    if update_laser and correct_for_laser_drift:
                        fout.write('Gravity value adjusted by ' +
                                   '{:0.2f}'.format(laser_corr * -1) +
                                   ' uGal for laser drift correction\n')
                        fout.write('Drift rate was ' +
                                   '{:0.4f}'.format(drift_rate) +
                                   ' microGal/day\n')
                        fout.write('Previous calibration was ' +
                                   '{:.0f}'.format(elapsed_days) +
                                   ' days prior to measurement\n\n')

                    if update_SM and correct_for_sm:
                        fout.write('Gravity value adjusted by ' +
                                   '{:0.2f}'.format(sm_corr * -1) +
                                   ' uGal for soil moisture correction\n')
                        fout.write('Soil moisture in the root zone (0-100 cm) was ' +
                                   '{:0.2f}'.format(sm_at_time_of_g) +
                                   '; the mean value was ' +
                                   '{:0.2f}'.format(sm.mean()) + '\n\n')
                    if update_SM or update_laser:
                        if write_corrections_to_file:
                            fid.write(station +
                                      ',' + dt.strftime("%Y-%m-%d") +
                                      ',' + '{:0.2f}'.format(laser_corr * -1) +
                                      ',' + '{:0.4f}'.format(drift_rate) +
                                      ',' + '{:.0f}'.format(elapsed_days) + '\n')

                os.system('cp temp.txt "' + fname + '"')
                os.system('rm temp.txt')
fid.close()