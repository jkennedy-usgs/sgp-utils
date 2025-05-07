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
import datetime as dt

#config = configparser.ConfigParser()
#config.read('fg5_parse.ini')
SKIP_UNPUBLISHED = True
#SKIP_UNPUBLISHED = config.getboolean('Parameters', 'SKIP_UNPUBLISHED')
#if QC_MODE := config.getboolean('Parameters', 'QC_MODE'):
#    print("Running in QC mode (edit parse_fg5.ini to change).")
pwd = os.getcwd()
gravity_data_archive = r"\\Igswztwwgszona\Gravity Data Archive"
polar_motion_spreadsheet = f"'{gravity_data_archive}\\QAQC\\[finals.data.xlsx]Sheet1'"
calibration_spreadsheet = f"'{gravity_data_archive}\\Absolute Data" + \
                          r"\A-10\Instrument Maintenance\Calibrations" + \
                          r"\[A10-008 clock and laser calibrations.xlsx]calibrations'"

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
    |True Polar(x)|True Polar(y)|True red laser|True blue laser\
    |True clock|Comments\n"
    header = header_string.split('|')
    #if QC_MODE:
    #    fout_string = "StudyArea\t" + fout_string
    #fout.write(fout_string)

    
    all_data = parse(data_directory)

    out = []
    out.append(header_string)
    out += all_data
    df = pd.DataFrame(all_data, columns=header)
    writer = pd.ExcelWriter(filesavename,
                            engine='xlsxwriter',
                            datetime_format='m/d/yyyy',
                            engine_kwargs={'options': {'strings_to_numbers': True}})

    df.to_excel(writer, sheet_name='Data', index=False)
    # workbook = writer.book
    # worksheet = writer.sheets['Data']
    #
    # formatdict = {'num_format': 'mm/dd/yyyy'}
    # fmt = workbook.add_format(formatdict)
    #
    # worksheet.set_column('AG:AG', None, fmt)

    writer.close()
    # Write data_row to file
    #for measurement in all_data:
    #    for each_element in measurement:
    #       fout.write(each_element + "\t")
    #    fout.write('\n')
    #fout.close()
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
                data_row.append(rf'=IF(OR(ISNUMBER(SEARCH("Gravity value not adjusted",AW{row})), ISNUMBER(SEARCH("Gravity value adjusted",AW{row}))),"",1)')
                data_row.append(study_area)

                # Look for these words in the g file
                tags = re.compile(r'Created|Setup|SN' +
                                  r'|Transfer|Actual|Time|TimeOffset|Nominal|Red' +
                                  r'|Blue|Scatter|SetsColl|SetsProc|Precision|BarPresCorr|Total_unc')

                # Dates need to be converted so excel can read them
                Date_tag = re.compile(r'Date')

                # 'Lat' is special because there are three data on the same line:
                # (Lat, Long, Elev)
                Lat_tag = re.compile(r'Lat')

                # 'Polar' is also special, for the same reason
                Pol_tag = re.compile(r'Polar')

                version = 0
                Version_tag = re.compile(r'Version')

                # Need this to accommodate station names with spaces
                Project_tag = re.compile(r'Project')
                Name_tag = re.compile(r'Name')

                # Apparently using a delta file is optional, it's not always written
                # to the .project file
                Delta_tag = re.compile(r'DFFile')
                OL_tag = re.compile(r'OLFile')
                Rub_tag = re.compile(r'RubFrequency')
                Grav_tag = re.compile(r'Grv')
                Grad_tag = re.compile(r'Gradient')

                # This one, because "Gradient:" is repeated exactly in this section
                Unc_tag = re.compile(r'Uncertainties')

                # This deals with multi-line comments
                Comment_tag = re.compile(r'Comments')
                comments = ''

                for line in project_file:
                    # Change up some text in the g file to make it easier to parse
                    # (remove duplicates, etc.)
                    line = str.strip(line)
                    line = str.replace(line, '\n\n', '\n')

                    Comment_tag_found = re.search(Comment_tag, line)
                    if inComments:
                        if comments == '':
                            comments = line
                        else:
                            comments += ' | '
                            comments += line
                        continue
                    elif Comment_tag_found is not None:
                        inComments = True
                        continue

                    line = str.replace(line, ":  ", ": ")
                    # Repeat to take care of ":   " (three spaces)
                    line = str.replace(line, ":  ", ": ")
                    line = str.replace(line, ":  ", ": ")
                    line = str.replace(line, "g Acquisition Version", "Acq")
                    line = str.replace(line, "g Processing ", "")
                    line = str.replace(line, "Project Name:", "Project")
                    line = str.replace(line, "File Created:", "Created")
                    line = str.replace(line, 'Gravity Corrections', 'grvcorr')
                    line = str.replace(line, " Height:", ":")
                    line = str.replace(line, "Delta Factor Filename:", "DFFile")
                    line = str.replace(line, "Ocean Load ON, Filename:", "OLFile")
                    line = str.replace(line, "Nominal Air Pressure:", "Nominal")
                    line = str.replace(line, "Barometric Admittance Factor:",
                                       "Admittance")
                    line = str.replace(line, " Motion Coord:", "")
                    line = str.replace(line, "Set Scatter:", "Scatter")
                    line = str.replace(line, "Offset:", "ofst")
                    line = str.replace(line, "Time Offset (D h:m:s):", "TimeOffset")
                    line = str.replace(line, "Ocean Load:", "OLC")
                    line = str.replace(line, "Rubidium Frequency:", "RubFrequency")
                    line = str.replace(line, "Blue Lock:", "Blue")
                    line = str.replace(line, "Red Lock:", "Red")
                    line = str.replace(line, "Red/Blue Separation:", "Separation")
                    line = str.replace(line, "Red/Blue Interval:", "Interval")
                    line = str.replace(line, "Gravity Corrections", "Corrections")
                    line = str.replace(line, "Gravity:", "Grv:")
                    line = str.replace(line, "Number of Sets Collected:", "SetsColl")
                    line = str.replace(line, "Number of Sets Processed:", "SetsProc")
                    # This is the PM error, not the values
                    line = str.replace(line, "Polar Motion:", "PolMotC")
                    line = str.replace(line, "Barometric Pressure:", "BarPresCorr")
                    line = str.replace(line, "System Setup:", "")
                    line = str.replace(line, "Total Uncertainty:", "Total_unc")
                    line = str.replace(line, "Measurement Precision:", "Precision")
                    line = str.replace(line, "Meter S/N:", "SN")
                    line = str.replace(line, ":", "", 1)
                    line = str.replace(line, ",", "")
                    line_elements = str.split(line, " ")

                    # Look for tags
                    tags_found = re.search(tags, line)
                    Lat_tag_found = re.search(Lat_tag, line)
                    Pol_tag_found = re.search(Pol_tag, line)
                    Version_tag_found = re.search(Version_tag, line)
                    Delta_tag_found = re.search(Delta_tag, line)
                    OL_tag_found = re.search(OL_tag, line)
                    Grav_tag_found = re.search(Grav_tag, line)
                    Unc_tag_found = re.search(Unc_tag, line)
                    Grad_tag_found = re.search(Grad_tag, line)
                    Rub_tag_found = re.search(Rub_tag, line)
                    Name_tag_found = re.search(Name_tag, line)
                    Project_tag_found = re.search(Project_tag, line)
                    Date_tag_found = re.search(Date_tag, line)

                    if Unc_tag_found is not None:
                        skip_grad = True

                    if Grad_tag_found is not None:
                        if not skip_grad:
                            data_row.append(line_elements[1])

                    # Old g versions don't output Time Offset, which comes right
                    # before gravity
                    if Grav_tag_found is not None:
                        if version < 5:
                            data_row.append('-999')
                        data_row.append(line_elements[1])

                    if Delta_tag_found is not None:
                        dtf = True
                        df = " ".join(line_elements[1:])

                    if OL_tag_found is not None:
                        olf = True
                        of = " ".join(line_elements[1:])

                    if Rub_tag_found is not None:
                        if dtf:
                            data_row.append(df)
                        else:
                            data_row.append('-999')
                        if olf:
                            data_row.append(of)
                        else:
                            data_row.append('-999')
                        data_row.append(line_elements[1])

                    if Version_tag_found is not None:
                        version = float(line_elements[1])

                    if Name_tag_found is not None or Project_tag_found is not None:
                        try:
                            name = " ".join(line_elements[1:])
                            data_row.append(name)
                        except:
                            data_row.append('-999')

                    if tags_found is not None:
                        try:
                            data_row.append(line_elements[1])
                        except:
                            data_row.append('-999')

                    if Date_tag_found is not None:
                        data_row.append(dt.datetime.strptime(line_elements[1],"%m/%d/%y")) #.strftime('%m/%d/%Y'))

                    if Lat_tag_found is not None:
                        data_row.append(line_elements[1])
                        data_row.append(line_elements[3])
                        data_row.append(line_elements[5])
                        # This accommodates old versions of g. If these data are to
                        # be published, though, they should be reprocessed in a more
                        # recent version.
                        if version < 5:
                            data_row.append('-999')  # Setup Height
                            data_row.append('-999')  # Transfer Height
                            data_row.append('-999')  # Actual Height

                    if Pol_tag_found is not None:
                        data_row.append(line_elements[1])
                        data_row.append(line_elements[3])
                        # if version < 5:
                        #     data_row.append('-999') # delta factor filename

                    if inComments > 0:
                        comments = comments + line
                        if inComments > 1:
                            comments = comments + ' | '
                        inComments += inComments

                    if Comment_tag_found is not None:
                        inComments = 1
                        comments = ''

                # Old g versions don't output transfer height correction
                if version < 5:
                    data_row.append('-999')

                # This adds an Excel formula that looks up the correct polar motion

                data_row.append(rf"=XLOOKUP(AH{row},{polar_motion_spreadsheet}!$F$1:$F$20000,{polar_motion_spreadsheet}!$G$1:$G$20000)")
                data_row.append(rf"=XLOOKUP(AH{row},{polar_motion_spreadsheet}!$F$1:$F$20000,{polar_motion_spreadsheet}!$I$1:$I$20000)")
                # Lookup red and blue laser calibrations
                data_row.append(rf"=XLOOKUP(AH{row},{calibration_spreadsheet}!$A$2:$A$200,{calibration_spreadsheet}!$E$2:$E$200,0,-1)")
                data_row.append(rf"=XLOOKUP(AH{row},{calibration_spreadsheet}!$A$2:$A$200,{calibration_spreadsheet}!$D$2:$D$200,0,-1)")
                # Lookup clock calibration
                data_row.append(rf"=XLOOKUP(AH{row},{calibration_spreadsheet}!$A$2:$A$200,{calibration_spreadsheet}!$C$2:$C$200,0,-1)")

                data_row.append(comments)
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
