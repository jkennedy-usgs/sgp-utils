#! python3
""""
Script to parse A10 files and create a tab-delimited file with the most
important data.

Should work with g8 and g9.

Jeff Kennedy
USGS
"""

import re
import os
from tkinter import filedialog
from tkinter import Tk
from time import strftime
import configparser

config = configparser.ConfigParser()
config.read('fg5_parse.ini')
SKIP_UNPUBLISHED = config.getboolean('Parameters', 'SKIP_UNPUBLISHED')

gravity_data_archive = "E:\\Shared\\Gravity Data Archive\\A-10"
pd = os.getcwd()
# gravity_data_archive = "X:\\Absolute Data\\A-10"

def launch_gui():
    root = Tk()
    root.withdraw()
    data_directory = filedialog.askdirectory(
        parent=root, initialdir=pd)
    a = data_directory.split('/')

    # For testing
    # data_directory = "E:\\Shared\\current\\python\\AZWSC_Gravity\\TAMA"
    # a = ['junk','TAMA']

    # File save name is directory plus time and date
    print(str(data_directory))
    if str.find(str(data_directory), 'Working') > 0:
        filesavename = os.getcwd() + '/working_dir/' + a[-1] + '_Working_' + \
                       strftime("%Y%m%d-%H%M") + '.txt'
    elif str.find(str(data_directory), 'Final') > 0:
        filesavename = os.getcwd() + '/working_dir/' + a[-1] + '_Final_' + \
                       strftime("%Y%m%d-%H%M") + '.txt'
    else:
        filesavename = os.getcwd() + '/working_dir/' + a[-1] + '_' + \
                       strftime("%Y%m%d-%H%M") + '.txt'



    # open file for overwrite (change to "r" to append)
    fout = open(filesavename, "w")

    # write data descriptor file header
    fout.write("Created\tProject\tStation Name\tLat\tLong\tElev\tSetup Height\
    \tTransfer Height\tActual Height\tGradient\tNominalAP\tPolar(x)\tPolar(y)\
    \tDF File\tOL File\tClock\tBlue\tRed\tDate\tTime\tTime Offset\tGravity\tSet Scatter\
    \tPrecision\tUncertainty\tCollected\tProcessed\tTransfer ht corr\tBaro corr\
    \tPolar(x) error\tPolar(y) error\\tlaser(blue) error\tBlue laser err\
    \tclock error\tComments\n")

    all_data = parse(data_directory)

    # Write data_array to file
    for measurement in all_data:
        for each_element in measurement:
            fout.write(each_element + "\t")
        fout.write('\n')
    fout.close()

def parse(data_directory):
    all_data = []
    output_line = 0
    inComments = 0
    # For each file in the data_directory
    for dirname, dirnames, filenames in os.walk(data_directory):
        if SKIP_UNPUBLISHED:
            if 'unpublished' in dirnames:
                dirnames.remove('unpublished')
        for filename in filenames:
            fname = os.path.join(dirname, filename)
            # If the file name ends in "project.txt"
            if str.find(fname, 'project.txt') != -1:
                print(fname)
                dtf = False
                olf = False
                skip_grad = False
                project_file = open(fname)
                data_descriptor = 0
                data_array = []  # ['a']*32
                # Look for these words in the g file
                tags = re.compile(r'Created|Setup' +
                                  r'|Transfer|Actual|Date|Time|TimeOffset|Nominal|Red' +
                                  r'|Blue|Scatter|SetsColl|SetsProc|Precision|BarPresCorr|Total_unc')
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

                # Apparently using a delta file is optional, it's not always written to the .project file
                Delta_tag = re.compile(r'DFFile')
                OL_tag = re.compile(r'OLFile')
                Rub_tag = re.compile(r'RubFrequency')
                Grav_tag = re.compile(r'Grv')
                Grad_tag = re.compile(r'Gradient')

                # This one, because "Gradient:" is repeated exactly in this section
                Unc_tag = re.compile(r'Uncertainties')

                # This deals with multi-line comments
                Comment_tag = re.compile(r'Comments')

                for line in project_file:
                    # Change up some text in the g file to make it easier to parse
                    # (remove duplicates, etc.)
                    line = str.strip(line)
                    line = str.replace(line, '\n\n', '\n')
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
                    line = str.replace(line, "Barometric Admittance Factor:", "Admittance")
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
                    line = str.replace(line, "Polar Motion:", "PolMotC")  # This is the PM error, not the values
                    line = str.replace(line, "Barometric Pressure:", "BarPresCorr")
                    line = str.replace(line, "System Setup:", "")
                    line = str.replace(line, "Total Uncertainty:", "Total_unc")
                    line = str.replace(line, "Measurement Precision:", "Precision")
                    line = str.replace(line, ":", "", 1)
                    line = str.replace(line, ",", "")
                    line_elements = str.split(line, " ")

                    # Look for tags
                    tags_found = re.search(tags, line)
                    Lat_tag_found = re.search(Lat_tag, line)
                    Pol_tag_found = re.search(Pol_tag, line)
                    Comment_tag_found = re.search(Comment_tag, line)
                    Version_tag_found = re.search(Version_tag, line)
                    Delta_tag_found = re.search(Delta_tag, line)
                    OL_tag_found = re.search(OL_tag, line)
                    Grav_tag_found = re.search(Grav_tag, line)
                    Unc_tag_found = re.search(Unc_tag, line)
                    Grad_tag_found = re.search(Grad_tag, line)
                    Rub_tag_found = re.search(Rub_tag, line)
                    Name_tag_found = re.search(Name_tag, line)
                    Project_tag_found = re.search(Project_tag, line)

                    if Unc_tag_found is not None:
                        skip_grad = True

                    if Grad_tag_found is not None:
                        if not skip_grad:
                            data_array.append(line_elements[1])

                    # Old g versions don't output Time Offset, which comes right before gravity
                    if Grav_tag_found is not None:
                        if version < 5:
                            data_array.append('-999')
                        data_array.append(line_elements[1])

                    if Delta_tag_found is not None:
                        dtf = True
                        df = " ".join(line_elements[1:])

                    if OL_tag_found is not None:
                        olf = True
                        of = " ".join(line_elements[1:])

                    if Rub_tag_found is not None:
                        if dtf:
                            data_array.append(df)
                        else:
                            data_array.append('-999')
                        if olf:
                            data_array.append(of)
                        else:
                            data_array.append('-999')
                        data_array.append(line_elements[1])

                    if Version_tag_found is not None:
                        version = float(line_elements[1])

                    if Name_tag_found is not None or Project_tag_found is not None:
                        try:
                            name = ''
                            name += line_elements[1].strip()
                            if len(line_elements) > 2:
                                for idx, item in enumerate(line_elements):
                                    if idx > 1:
                                        name += '_'
                                        name += item.strip()
                            data_array.append(name)
                        except:
                            data_array.append('-999')

                    if tags_found is not None:
                        try:
                            data_array.append(line_elements[1])
                        except:
                            data_array.append('-999')

                    if Lat_tag_found is not None:
                        data_array.append(line_elements[1])
                        data_array.append(line_elements[3])
                        data_array.append(line_elements[5])
                        # This accommodates old versions of g. If these data are to be published,
                        # though, they should be reprocessed in a more recent version.
                        if version < 5:
                            data_array.append('-999')  # Setup Height
                            data_array.append('-999')  # Transfer Height
                            data_array.append('-999')  # Actual Height

                    if Pol_tag_found is not None:
                        data_array.append(line_elements[1])
                        data_array.append(line_elements[3])
                        # if version < 5:
                        #     data_array.append('-999') # delta factor filename

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
                    data_array.append('-999')
                # This adds an Excel formula that looks up the correct polar motion
                data_array.append(r"=VLOOKUP(S" + str(output_line + 2) +
                                  ",'\\\\Igswzcwwwsjeffk\Shared\Gravity\[finals.data.xlsx]Sheet1'" +
                                  "!$F$1:$G$20000,2,FALSE)-L" + str(output_line + 2))
                data_array.append("=VLOOKUP(S" + str(output_line + 2) +
                                  ",'\\\\Igswzcwwwsjeffk\Shared\Gravity\[finals.data.xlsx]Sheet1'" +
                                  "!$F$1:$I$20000,4,FALSE)-M" + str(output_line + 2))
                data_array.append("=VLOOKUP(S" + str(output_line + 2) +
                                  ",'\\\\Igswztwwgszona\Gravity Data Archive\Absolute Data\A-10\Instrument Maintenance" +
                                  "\Calibrations\[A10-008 clock and laser calibrations.xlsx]calibrations'" +
                                  "!$A$2:$D$20,3,TRUE)-Q" + str(output_line + 2))
                data_array.append("=VLOOKUP(S" + str(output_line + 2) +
                                  ",'\\\\Igswztwwgszona\Gravity Data Archive\Absolute Data\A-10\Instrument Maintenance" +
                                  "\Calibrations\[A10-008 clock and laser calibrations.xlsx]calibrations'" +
                                  "!$A$2:$D$20,2,TRUE)-P" + str(output_line + 2))

                data_array.append(comments)

                project_file.close()
                output_line = output_line + 1
                all_data.append(data_array)
    return all_data

if __name__ == "__main__":
    launch_gui()