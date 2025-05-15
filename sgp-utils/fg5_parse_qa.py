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
import pandas as pd
# import configparser
from fg5 import project_to_list

SKIP_UNPUBLISHED = True
pwd = os.getcwd()
gravity_data_archive = r"X:"
polar_motion_spreadsheet = f"'{gravity_data_archive}\\QAQC\\[finals.data.xlsx]Sheet1'"
calibration_spreadsheet = f"'{gravity_data_archive}\\Absolute Data" + \
                          r"\A-10\Instrument Maintenance\Calibrations" + \
                          r"\[A10-008 clock and laser calibrations.xlsx]calibrations'"

# These are the polynomial coefficients for a linear function that calculates nominal AP
# as a function of elevation
pm_pars = [-1.35032E-10, 5.76387E-06, -0.120136869, 1013.251572]

def launch_gui():
    root = Tk()
    root.withdraw()
    data_directory = filedialog.askdirectory(
        parent=root, initialdir=pwd)

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

    filesavename = os.path.join(od, a[-1] + dd + "QA_" + strftime("%Y%m%d-%H%M") + '.xlsx')
    print(f'Saving {filesavename}')
    # open file for overwrite (change to "r" to append)
    # fout = open(filesavename, "w")

    # write data descriptor file header
    header_string = "Nominal AP check|DF check|OL check|g check|Lat check|Lon check\
    |Elev check|Polar(x) check|Polar(y) check|Red laser check|Blue laser check\
    |clock check|Laser correction check\
    |Study area|Created|Project|Station Name|Lat|Lon|Elev|Setup Height\
    |Transfer Height|Actual Height|Gradient|NominalAP|Polar(x)|Polar(y)|Meter SN\
    |DF File|OL File|Clock|Blue|Red|Date|Time|Time Offset|Gravity|Set Scatter\
    |Precision|Uncertainty|Collected|Processed|Baro corr|Transfer ht corr\
    |Comments|True Polar(x)|True Polar(y)|True red laser|True blue laser\
    |True clock\n"
    header = header_string.split('|')

    all_data = parse(data_directory)

    out = []
    out.append(header_string)
    out += all_data
    df = pd.DataFrame(all_data, columns=header)
    df.insert(len(df.columns)-1, 'Comments', df.pop('Comments'))
    df['Date'] = pd.to_datetime(df['Date'])
    writer = pd.ExcelWriter(filesavename,
                            engine='xlsxwriter',
                            datetime_format='m/d/yyyy', # this only applies if dates are dt.datetimes, which they're not (they're strings)
                            engine_kwargs={'options': {'strings_to_numbers': True}})

    df.to_excel(writer, sheet_name='Data', index=False)
    # workbook = writer.book
    # worksheet = writer.sheets['Data']
    #
    # formatdict = {'num_format': 'm/d/yyyy'}
    # fmt = workbook.add_format(formatdict)
    #
    # worksheet.set_column('AH:AH', None, fmt)

    writer.close()

    print(f'Output file written: {filesavename}')


def parse(data_directory):
    all_data = []
    # counter for Excel formulas
    row = 2  # +1 for the header row, and +1 because Excel is 1-based

    # For each file in the data_directory
    for dirname, dirnames, filenames in os.walk(data_directory):
        if SKIP_UNPUBLISHED:
            if 'unpublished' in dirnames:
                dirnames.remove('unpublished')
        for filename in filenames:
            fname = os.path.join(dirname, filename)
            inComments = 0
            # If the file name ends in "project.txt"
            if str.find(fname, 'project.txt') == -1:
                continue
            try:        
                study_area = (os.path.normpath(dirname).split(os.path.sep)[4])
            except IndexError:
                # tempfix: study area is at C:\
                study_area = (os.path.normpath(dirname).split(os.path.sep)[1])
            print(filename)
            dtf = False
            olf = False
            skip_grad = False
            with open(fname) as project_file:
                data_row = []
                data_row.append(rf'=IF(ABS(Y{row}-(T{row}^3*{pm_pars[0]}+T{row}^2*{pm_pars[1]}+T{row}*{pm_pars[2]}+{pm_pars[3]}))>0.01,1,"")')
                data_row.append(rf'=IF(ISNUMBER(SEARCH(Q{row},AC{row})),"",1)')
                data_row.append(rf'=IF(ISNUMBER(SEARCH(Q{row},AD{row})),"",1)')
                data_row.append(rf'=IF($Q{row}=$Q{row-1},IF(ABS(AK{row}-AK{row-1})>50,1,""),"")')
                data_row.append(rf'=IF($Q{row}=$Q{row-1},IF(R{row}=R{row-1},"",1),"")')
                data_row.append(rf'=IF($Q{row}=$Q{row-1},IF(S{row}=S{row-1},"",1),"")')
                data_row.append(rf'=IF($Q{row}=$Q{row-1},IF(T{row}=T{row-1},"",1),"")')
                data_row.append(rf'=IF(ABS(AS{row}-Z{row})>0.005,1,"")')
                data_row.append(rf'=IF(ABS(AT{row}-AA{row})>0.005,1,"")')
                data_row.append(rf'=IF(ABS(AU{row}-AG{row})>0.0000000001,1,"")')
                data_row.append(rf'=IF(ABS(AV{row}-AF{row})>0.0000000001,1,"")')
                data_row.append(rf'=IF(ABS(AW{row}-AE{row})>0.0001, 1, "")')
                data_row.append(rf'=IF(OR(ISNUMBER(SEARCH("Gravity value not adjusted",AX{row})), ISNUMBER(SEARCH("Gravity value adjusted",AX{row}))),"",1)')
                data_row.append(study_area)
            # This adds an Excel formula that looks up the correct polar motion

                data_row += project_to_list(project_file)

                data_row.append(rf"=XLOOKUP(AH{row},{polar_motion_spreadsheet}!$F$1:$F$20000,{polar_motion_spreadsheet}!$G$1:$G$20000)")
                data_row.append(rf"=XLOOKUP(AH{row},{polar_motion_spreadsheet}!$F$1:$F$20000,{polar_motion_spreadsheet}!$I$1:$I$20000)")
                # Lookup red and blue laser calibrations
                data_row.append(rf"=XLOOKUP(AH{row},{calibration_spreadsheet}!$A$2:$A$200,{calibration_spreadsheet}!$E$2:$E$200,0,-1)")
                data_row.append(rf"=XLOOKUP(AH{row},{calibration_spreadsheet}!$A$2:$A$200,{calibration_spreadsheet}!$D$2:$D$200,0,-1)")
                # Lookup clock calibration
                data_row.append(rf"=XLOOKUP(AH{row},{calibration_spreadsheet}!$A$2:$A$200,{calibration_spreadsheet}!$C$2:$C$200,0,-1)")
                row += 1
                all_data.append(data_row)
    return all_data


if __name__ == "__main__":
    print(sys.argv)
    if len(sys.argv) == 1:
        directory = launch_gui()
    else:
        directory = sys.argv[1]
    df = parse_data(directory, output_dir=directory)
