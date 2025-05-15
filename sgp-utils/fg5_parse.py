#! python3
""""
Script to parse A10 files and create a tab-delimited file with the most
important data.

Reads parameters from fg5_parse.ini:
SKIP_UNPUBLISHED: ignores files with "unpublished' in the directory path
QC_MODE: adds extra columns; for copy/pasting into Excel QA worksheet

Should work with g8 and g9.

Jeff Kennedy
USGS
"""

import re
import os
import sys
from tkinter import filedialog
from tkinter import Tk
from time import strftime
import configparser
from fg5 import project_to_list

# config = configparser.ConfigParser()
# config.read('fg5_parse.ini')
# SKIP_UNPUBLISHED = config.getboolean('Parameters', 'SKIP_UNPUBLISHED')
# if QC_MODE := config.getboolean('Parameters', 'QC_MODE'):
#     print("Running in QC mode (edit parse_fg5.ini to change).")
pd = os.getcwd()
gravity_data_archive = r"\\Igswztwwgszona\Gravity Data Archive"
polar_motion_spreadsheet = f"'{gravity_data_archive}\\QAQC\\[finals.data.xlsx]Sheet1'"
calibration_spreadsheet = f"'{gravity_data_archive}\\Absolute Data" + \
                          r"\A-10\Instrument Maintenance\Calibrations" + \
                          r"\[A10-008 clock and laser calibrations.xlsx]calibrations'"


def launch_gui():
    root = Tk()
    root.withdraw()
    data_directory = filedialog.askdirectory(
        parent=root, initialdir=pd)

    return data_directory


def parse_data(data_directory, output_dir=None):
    # For testing
    # data_directory = "E:\\Shared\\current\\python\\AZWSC_Gravity\\TAMA"
    # a = data_directory.split('/')
    a = os.path.split(data_directory)
    # File save name is directory plus time and date
    print(str(data_directory))
    if output_dir:
        od = output_dir
    elif os.getcwd() == os.path.normpath(r'C:\sgp-utils\sgp-utils'):
        od = os.path.join(os.getcwd(), 'working_dir')
    else:
        od = os.getcwd()

    if str.find(str(data_directory), 'Working') > 0:
        dd = '_Working_'
    elif str.find(str(data_directory), 'Final') > 0:
        dd = '_Final_'
    else:
        dd = '_'

    filesavename = os.path.join(od, a[-1] + dd + strftime("%Y%m%d-%H%M") + '.txt')
    print(f'Saving {filesavename}')
    # open file for overwrite (change to "r" to append)
    fout = open(filesavename, "w")

    # write data descriptor file header
    fout_string = "Created\tProject\tStation Name\tLat\tLong\tElev\tSetup Height\
    \tTransfer Height\tActual Height\tGradient\tNominalAP\tPolar(x)\tPolar(y)\tSN\
    \tDF File\tOL File\tClock\tBlue\tRed\tDate\tTime\tTime Offset\tGravity\tSet Scatter\
    \tPrecision\tUncertainty\tCollected\tProcessed\tBaro corr\tTransfer ht corr\
    \tComments\n"

    fout.write(fout_string)

    all_data = parse(data_directory)

    # Write data_array to file
    for measurement in all_data:
        for each_element in measurement:
            fout.write(each_element + "\t")
        fout.write('\n')
    fout.close()
    print(f'Output file written: {filesavename}')
    return(filesavename)

def parse(data_directory):
    all_data = []
    output_line = 0

    # For each file in the data_directory
    for dirname, dirnames, filenames in os.walk(data_directory):
        if SKIP_UNPUBLISHED:
            if 'unpublished' in dirnames:
                dirnames.remove('unpublished')
        for filename in filenames:
            fname = os.path.join(dirname, filename)
            # If the file name ends in "project.txt"
            if str.find(fname, 'project.txt') == -1:
                continue

            with open(fname) as project_file:
                print(fname)
                data_array = project_to_list(project_file)
                # This adds an Excel formula that looks up the correct polar motion

                    # In non-QC_MODE, write the difference between the value used
                    # and the true value
                    # data_array.append(
                    #     r"=VLOOKUP(S{0},{1}!$F$1:$G$20000,2,FALSE)-L{2}".format(
                    #         str(output_line + 2), polar_motion_spreadsheet,
                    #         str(output_line + 2)))
                    # data_array.append(
                    #     "=VLOOKUP(S{0},{1}!$F$1:$I$20000,4,FALSE)-M{2}".format(
                    #         str(output_line + 2), polar_motion_spreadsheet,
                    #         str(output_line + 2)))
                    # # Lookup red and blue laser calibrations
                    # data_array.append(
                    #     "=VLOOKUP(S{0},{1}!$A$2:$E$200,5,TRUE)-R{2}".format(
                    #         str(output_line + 2), calibration_spreadsheet,
                    #         str(output_line + 2)))
                    # data_array.append(
                    #     "=VLOOKUP(S{0},{1}!$A$2:$E$200,4,TRUE)-Q{2}".format(
                    #         str(output_line + 2), calibration_spreadsheet,
                    #         str(output_line + 2)))
                    # data_array.append(
                    #     "=IF(ABS(VLOOKUP(S{0},{1}!$A$2:$E$200,2,TRUE)-P{2}) < 0.00001, 0, VLOOKUP(S{3},{4}!$A$2:$E$200,3,TRUE)-P{5})".format(
                    #         output_line + 2, calibration_spreadsheet,
                    #         output_line + 2, output_line + 2,
                    #         calibration_spreadsheet, output_line + 2))
                output_line += 1
                all_data.append(data_array)
    return all_data


if __name__ == "__main__":
    print(sys.argv)
    if len(sys.argv) == 1:
        directory = launch_gui()
    else:
        directory = sys.argv[1]
    out_file = parse_data(directory, output_dir=directory)
    with open(os.path.join("temp.txt")) as f:
        f.write(out_file)
