#! python3
# coding: utf-8

# Script to update g values in FG-5/A-10 .project.txt files with laser drift correction.
# 
# The script works on project.txt files in a specified directory (and subdirectories). The g value in each
# .project.txt file is updated, and a comment added that describes the magnitude of the correction. The original
# .project.txt file is copied to a new file, where 'project.txt' in the filename is replaced with 'original.txt'.
# 
# Laser drift corrections are taken from an Excel workbook, specified as a parameter in the script.

# A csv-file summary of the corrections is written, with the filename "Corrections_YYYY-MM-DD.csv"

# Scenarios:
#
# 1) .project.txt exists, *.original.txt does not
#       .project.txt already updated: do nothing
#       .project.txt not updated: copy proj > orig, update proj
#
# 2) .project.txt and original.txt both exist
#       .project.txt already updated with correct correction: do nothing
#       .project.txt file has incorrect correction: fix it
#       .project.txt not updated: copy proj > orig (overwrite), update proj
#
# 

import os
from tkinter import filedialog
from tkinter import *
import datetime
import pandas as pd  # xlrd 1.2.0 (OR LESS, NOT HIGHER!) must also be installed
from time import strftime

# User-specified options
update_laser = True
GDA = r'X:\Absolute Data\A-10\Final Data'
laser_cal_file = "\\\\Igswztwwgszona\\Gravity Data Archive\\Absolute Data\\A-10\\" + \
                 "Instrument Maintenance\\Calibrations\\A10-008 clock and laser calibrations.xlsx"
laser_cal_worksheet = "DRIFT LOOKUP TABLE"


def project_file_check_status(fn):
    """

    :param fn:
    :return: String status
               'done' = correction applied,
    """
    # Iterate through, looking for "Gravity value adjusted by" or "Gravity value not adjusted"

    with open(fn, 'r') as fid:
        for line in fid:
            if "Gravity value adjusted by" in line:
                return 'done', float(line.split()[4]) * -1
            elif "Gravity value not adjusted" in line:
                return 'check', 0.0
            else:
                continue
    return 'update', 0.0

    # if os.path.isfile(orig_fn):
    #     return


def get_laser_corr(dt, df_drift):
    for idx, row in df_drift.iterrows():
        if dt > row["BEGIN"]:
            if dt < row["END"]:
                drift_rate = row["MPD"]
                elapsed_days = dt - row["BEGIN"].to_pydatetime()
                elapsed_days = float(elapsed_days.days)
                laser_corr = elapsed_days * drift_rate
                return drift_rate, elapsed_days, laser_corr
    return 0, 0, 0


def project_file_get_date(project_file):
    with open(project_file, 'r') as f:
        for line in f:
            line_elements = line.split(" ")
            if line_elements[0] == "Date:":
                date_str = line_elements[-1]
                dt = datetime.datetime.strptime(date_str.strip(), "%m/%d/%y")
                return dt


def update_g(project_file, corr):
    """
    Get and apply (write to project.txt file) gravity correction.
    :param fout:
    :param project_file:
    :return:
    """
    with open('temp.txt', "w") as fout:
        with open(project_file, 'r') as fin:
            for line in fin:
                line_elements = line.split()
                if len(line_elements) > 0:
                    if line_elements[0] == "Gravity:":
                        g = float(line_elements[-2])
                        microGal_symbol = line_elements[-1]
                        corr_g = g - corr  # Typically laser_corr is negative, so this makes g larger
                        fout.write('Gravity: {:9.2f} {}\n'.format(corr_g, microGal_symbol))
                    else:
                        fout.write(line)
                else:
                    fout.write(line)

    os.system('cp temp.txt "' + fname + '"')
    os.system('rm temp.txt')


def remove_old_correction(fname, corr):
    update_g(fname, -1. * corr)


def remove_old_drift_comment(fname):
    with open("temp.txt", 'w') as fout:
        with open(fname, 'r') as fin:
            for line in fin:
                if "Gravity value adjusted by" in line:
                    continue
                elif "Drift rate was" in line:
                    continue
                elif "Previous calibration was" in line:
                    continue
                elif "Gravity value not adjusted" in line:
                    continue
                else:
                    fout.write(line)

    os.system('cp temp.txt "' + fname + '"')
    os.system('rm temp.txt')


def update_file(fid, fname, drift_rate=0, elapsed_days=0, laser_corr=0):
    """
    Update gravity value and write correction details at end of *.project.txt file and in corrections file.
    :param write_corrections_to_file:
    :param fid:
    :return:
    """

    copy_to_original_txt(fname)
    update_g(fname, laser_corr)
    append_calibration_comment(laser_corr, drift_rate, elapsed_days, fname)
    append_calibration_to_csv(laser_corr, drift_rate, elapsed_days, fid, station)


def copy_to_original_txt(fname):
    fn = fname.replace('project','original')
    os.system(f'cp "{fname}" "{fn}"')


def project_file_stationname(fname):
    with open(fname, 'r') as fid:
        for line in fid:
            line_elements = line.split()
            if len(line_elements) > 1:
                if line_elements[0] == "Name:":
                    return ' '.join(line_elements[1:])
    return None


def append_calibration_comment(laser_corr, drift_rate, elapsed_days, fname):
    with open(fname, "a") as fout:
        if elapsed_days == 0 or abs(laser_corr) < 0.0001:
            fout.write('Gravity value not adjusted (no valid calibration data for the time period)\n')
            return
        else:
            fout.write('Gravity value adjusted by ' +
                       '{:0.2f}'.format(laser_corr * -1) +
                       ' uGal for laser drift correction\n')
            fout.write('Drift rate was ' +
                       '{:0.4f}'.format(drift_rate) +
                       ' microGal/day\n')
            fout.write('Previous calibration was ' +
                       '{:.0f}'.format(elapsed_days) +
                       ' days prior to measurement\n\n')


def append_calibration_to_csv(laser_corr, drift_rate, elapsed_days, fid, station):
    fid.write(station +
              ',' + dt.strftime("%Y-%m-%d") +
              ',' + '{:0.2f}'.format(laser_corr * -1) +
              ',' + '{:0.4f}'.format(drift_rate) +
              ',' + '{:.0f}'.format(elapsed_days) + '\n')


if __name__ == "__main__":
    root = Tk()
    root.withdraw()
    data_directory = filedialog.askdirectory(
        parent=root, initialdir=GDA)
    # data_directory = u'\\\\Igswztwwgszona\\Gravity Data Archive\\Absolute Data\\A-10\\Final Data\\Big Chino'

    xl = pd.ExcelFile(laser_cal_file)
    drift_xl_sheet = xl.parse(laser_cal_worksheet)

    # File save name is directory plus time and date
    fid = open('.\working_dir\Corrections_' + strftime("%Y%m%d-%H%M") + '.csv', 'w')
    fid.write('Station,Date,Drift_corr,Drift_rate,Elapsed_days_since_cal,SM_corr,SM,SM_mean\n')


    # For each file in the data_directory and subdirectories
    for dirname, dirnames, filenames in os.walk(data_directory):
        if 'unpublished' in dirname:
            continue
        for filename in filenames:
            fname = os.path.join(dirname, filename)
            # If the file name ends in "project.txt"
            if fname.find('project.txt') != -1:
                station = project_file_stationname(fname)
                status, orig_corr = project_file_check_status(fname)
                dt = project_file_get_date(fname)
                drift_rate, elapsed_days, laser_error = get_laser_corr(dt, drift_xl_sheet)
                if status == 'done':
                    # a laser correction has previously been applied
                    if abs(orig_corr - laser_error) < 0.05:
                        # check that it matches the current best value
                        print(f'{filename}: Correct ccrrection already applied')
                        continue
                    else:
                        # It's different. Remove the old and apply the new
                        remove_old_correction(fname, orig_corr)
                        remove_old_drift_comment(fname)
                        print(f'{filename}: Correction updated. Old = {orig_corr}, New = {laser_error}')
                        update_file(fid, fname, drift_rate, elapsed_days, laser_error)
                if status == 'check':
                    # previously no correction was applied, if there's one available now, apply it
                    if abs(laser_error) > 0.01:
                        remove_old_drift_comment(fname)
                        update_file(fid, fname, drift_rate, elapsed_days, laser_error)
                        print(f'{filename}: Prior correction was zero. New correction = {laser_error}')
                if status == 'update':
                    update_file(fid, fname, drift_rate, elapsed_days, laser_error)
                    print(f'{filename}: No prior correction. New correction = {laser_error}')

    fid.close()
