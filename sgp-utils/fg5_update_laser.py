#! python3
# coding: utf-8

# Script to update g values in FG-5/A-10 .project.txt files with laser drift correction.
#
# This is the QA version. It writes a .xslx file with various formulas to check results.
#
# The script works on project.txt files in a specified directory (and
# subdirectories). The g value in each .project.txt file is updated, and a comment
# added that describes the magnitude of the correction. The original .project.txt
# file is copied to a new file, where 'project.txt' in the filename is replaced with
# 'original.txt'.
#
# Laser drift corrections are taken from an Excel workbook.

# A csv-file summary of the corrections is written, with the filename
# "Corrections_YYYY-MM-DD.csv"

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

import os
from tkinter import filedialog
from tkinter import *
import datetime
import pandas as pd  # xlrd 1.2.0 (OR LESS, NOT HIGHER!) must also be installed
from time import strftime

from fg5 import A10
# User-specified options
update_laser = True

GDA = r'X:\\'
# New laser cal file April 2025
# Laser drift calculated as slope of a best-fit line. Drift rate in uGal/day is in
# cell H2. There is one sheet per meter; the sheet name is the laser SN
laser_cal_file = os.path.join(GDA, 'QAQC', 'Laser_calibration', 'LaserCalibration.xlsx')


def project_file_check_status(fn):
    """
    :param fn: String filename
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


def get_laser_corr(fg5, df):
    """
    We want to apply a laser correction based on the time since the last calibration and
    the drift rate.

    As of spring 2025, we are applying a laser drift correction based on the average
    laser drift (slope of a best-fit line), not just the drift calculated between a
    'before' and 'after' calibration.

    The .project.txt files might not necessarily use the most recent laser calibration,
    as calibrations happen more frequently than the template files on the laptop are
    updated.

    There are two relevant dates, that might be the same:
        1) The date of the laser calibration that corresponds to the laser frequencies
           in the .project.txt file. We want to pro-rate the drift based on this date.
        2) The date of the most recent laser calibration that occurred before the
           measurement. We report this date in the .project.txt comments as the "Date of
           last calibration".
    """
    try:
        df = df.set_index(['Red', 'Blue'])
        matching_laser_row = df.loc[(fg5.red, fg5.blue)]
        drift_rate = float(df.iloc[0, 5])
        df = df.set_index('Start Date')
        closest_prev_date = df.iloc[df.index.get_indexer([fg5.date], method='ffill')].index.values[0]
        days_since_last_cal = (datetime.datetime.strptime(fg5.date,"%Y-%m-%d") -
                               datetime.datetime.strptime(
                                   closest_prev_date,
                                   "%Y-%m-%d %H:%M:%S")).days
        days_to_prorate_laser = (datetime.datetime.strptime(fg5.date,"%Y-%m-%d") -
                        datetime.datetime.strptime(matching_laser_row['Start Date'], "%Y-%m-%d %H:%M:%S")).days
        laser_corr = days_to_prorate_laser * drift_rate
        return drift_rate, days_since_last_cal, laser_corr
    except:
        print('!!!!!!!!!!!! LASER CAL ERROR !!!!!!!!!!!!!!!!')
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
    :param project_file:
    :param corr:
    :return: None
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
                        fout.write(
                            'Gravity: {:9.2f} {}\n'.format(corr_g, microGal_symbol))
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
    fn = fname.replace('project', 'original')
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
            fout.write(
                'Gravity value not adjusted (no valid calibration data for the time period)\n')
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


def format_float_string(value):
    # Convert to float
    float_value = float(value)
    # Format the value to have exactly 7 decimal places
    return f"{float_value:.7f}"

if __name__ == "__main__":
    root = Tk()
    root.withdraw()
    data_directory = filedialog.askdirectory(
        parent=root, initialdir=GDA)
    # data_directory = r"C:\Heritage"

    xl = pd.ExcelFile(laser_cal_file)
    drift_sheets = dict()
    for sheet in xl.sheet_names:
        df = xl.parse(sheet, dtype=str)
        df['Red'] = df['Red'].apply(format_float_string)
        df['Blue'] = df['Blue'].apply(format_float_string)
        drift_sheets[sheet] = df

    # File save name is directory plus time and date
    fid = open(os.path.join(data_directory, 'Corrections_' + strftime("%Y%m%d-%H%M") + '.csv'), 'w')
    fid.write(
        'Station,Date,Drift_corr,Drift_rate,Elapsed_days_since_cal,SM_corr,SM,SM_mean\n')

    # For each file in the data_directory and subdirectories
    for dirname, dirnames, filenames in os.walk(data_directory):
        if 'unpublished' in dirname:
            continue
        for filename in filenames:
            fname = os.path.join(dirname, filename)

            # If the file name ends in "project.txt"
<<<<<<< Updated upstream
            if fname.find('project.txt') != -1:
                print(fname)
                prj_file = A10(fn=fname)
                station = project_file_stationname(fname)
                status, orig_corr = project_file_check_status(fname)
                dt = project_file_get_date(fname)
                drift_rate, elapsed_days, laser_error = get_laser_corr(prj_file,
                                                                       drift_sheets[prj_file.sn])
                if status == 'done':
                    # a laser correction has previously been applied
                    if abs(orig_corr - laser_error) < 0.02:
                        # check that it matches the current best value
                        print(f'{filename}: Correct correction already applied')
                        continue
                    else:
                        # It's different. Remove the old and apply the new
                        remove_old_correction(fname, orig_corr)
                        remove_old_drift_comment(fname)
                        print(
                            f'{filename}: Correction updated. Old = {orig_corr:.2f}, New = {laser_error:.2f}')
                        update_file(fid, fname, drift_rate, elapsed_days, laser_error)
                if status == 'check':
                    # previously no correction was applied, if there's one available now, apply it
                    if abs(laser_error) > 0.01:
                        remove_old_drift_comment(fname)
                        update_file(fid, fname, drift_rate, elapsed_days, laser_error)
                        print(
                            f'{filename}: Prior correction was zero. New correction = {laser_error:.2f}')
                if status == 'update':
=======
            if fname.find('project.txt') == -1:
                continue
            print(fname)
            station = project_file_stationname(fname)
            status, orig_corr = project_file_check_status(fname)
            dt = project_file_get_date(fname)
            drift_rate, elapsed_days, laser_error = get_laser_corr(dt,
                                                                   drift_xl_sheet)
            if status == 'done':
                # a laser correction has previously been applied
                if abs(orig_corr - laser_error) < 0.02:
                    # check that it matches the current best value
                    print(f'{filename}: Correct ccrrection already applied')
                    continue
                else:
                    # It's different. Remove the old and apply the new
                    remove_old_correction(fname, orig_corr)
                    remove_old_drift_comment(fname)
                    print(
                        f'{filename}: Correction updated. Old = {orig_corr:.2f}, New = {laser_error:.2f}')
                    update_file(fid, fname, drift_rate, elapsed_days, laser_error)
            if status == 'check':
                # previously no correction was applied, if there's one available now, apply it
                if abs(laser_error) > 0.01:
                    remove_old_drift_comment(fname)
>>>>>>> Stashed changes
                    update_file(fid, fname, drift_rate, elapsed_days, laser_error)
                    print(
                        f'{filename}: Prior correction was zero. New correction = {laser_error:.2f}')
            if status == 'update':
                update_file(fid, fname, drift_rate, elapsed_days, laser_error)
                print(
                    f'{filename}: No prior correction. New correction = {laser_error:.2f}')

    fid.close()
