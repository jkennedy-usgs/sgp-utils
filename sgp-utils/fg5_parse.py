""""
Script to parse A10 files and create a tab-delimited file with the most
important data.

Should work with g8 and g9.

Jeff Kennedy
USGS
"""

import string
import re
import os
import Tkinter, tkFileDialog
from time import strftime

gravity_data_archive = "E:\\Shared\\Gravity Data Archive\\A-10"
pd = os.getcwd()
##gravity_data_archive = "X:\\Absolute Data\\A-10"
root = Tkinter.Tk()
root.withdraw()
data_directory = tkFileDialog.askdirectory(
    parent=root,initialdir=pd)
a = data_directory.split('/')

### For testing
# data_directory = "E:\\Shared\\current\\python\\AZWSC_Gravity\\TAMA"
# a = ['junk','TAMA']

# File save name is directory plus time and date
print str(data_directory)
if str.find(str(data_directory), 'Working') > 0:
    filesavename = os.getcwd()  + '/wroking_dir/' + a[-1] + '_Working_' +\
      strftime("%Y%m%d-%H%M") + '.txt'
elif str.find(str(data_directory), 'Final') > 0:
    filesavename = os.getcwd()  + '/working_dir/' + a[-1] + '_Final_' +\
      strftime("%Y%m%d-%H%M") + '.txt'
else:
    filesavename = os.getcwd()  + '/working_dir/' + a[-1] + '_' +\
      strftime("%Y%m%d-%H%M") + '.txt'
      
      
output_line=0
inComments = 0

#open file for overwrite (change to "r" to append)
fout = open(filesavename,"w")

#write data descriptor file header
fout.write("Created\tProject\tStation Name\tLat\tLong\tElev\tSetup Height\
\tTransfer Height\tActual Height\tGradient\tNominalAP\tPolar(x)\tPolar(y)\
\tDF File\tOL File\tClock\tBlue\tRed\tDate\tTime\tTime Offset\tGravity\tSet Scatter\
\tPrecision\tUncertainty\tCollected\tProcessed\tTransfer ht corr\tBaro corr\
\tPolar(x) error\tPolar(y) error\\tlaser(blue) error\tclock error\tComments\n")

# For each file in the data_directory
for dirname,dirnames,filenames in os.walk(data_directory):
    if 'unpublished' in dirnames:
        dirnames.remove('unpublished')
    for filename in filenames:
        fname = os.path.join(dirname, filename)
        # If the file name ends in "project.txt"
        if string.find(fname,'project.txt') != -1:
            print fname
            dtf = False
            olf = False
            skip_grad = False
            project_file = open(fname)
            data_descriptor = 0
            data_array = [] #['a']*32
            # Look for these words in the g file
            tags = re.compile(r'Created|Setup'+
            r'|Transfer|Actual|Date|Time|TimeOffset|Nominal|Red'+
            r'|Blue|Scatter|SetsColl|SetsProc|Precision|BarPresCorr|Total_unc')
            # 'Lat' is special because there are three data on the same line:
            # (Lat, Long, Elev)
            Lat_tag = re.compile(r'Lat')

            #'Polar' is also special, for the same reason
            Pol_tag = re.compile(r'Polar')

            Version_tag = re.compile(r'Version')

            # Need this to accomodate station names with spaces
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
                line = string.strip(line)
                line = string.replace(line,'\n\n','\n')
                line = string.replace(line,":  ",": ")
                # Repeat to take care of ":   " (three spaces)
                line = string.replace(line,":  ",": ")
                line = string.replace(line,":  ",": ")
                line = string.replace(line,"g Acquisition Version","Acq")
                line = string.replace(line,"g Processing ","")
                line = string.replace(line,"Project Name:","Project")
                line = string.replace(line,"File Created:","Created")
                line = string.replace(line,'Gravity Corrections','grvcorr')
                line = string.replace(line," Height:",":")
                line = string.replace(line,"Delta Factor Filename:","DFFile")
                line = string.replace(line,"Ocean Load ON, Filename:","OLFile")
                line = string.replace(line,"Nominal Air Pressure:","Nominal")
                line = string.replace(line,"Barometric Admittance Factor:","Admittance")
                line = string.replace(line," Motion Coord:","")
                line = string.replace(line,"Set Scatter:","Scatter")
                line = string.replace(line,"Offset:","ofst")
                line = string.replace(line,"Time Offset (D h:m:s):","TimeOffset")
                line = string.replace(line,"Ocean Load:","OLC")
                line = string.replace(line,"Rubidium Frequency:","RubFrequency")
                line = string.replace(line,"Blue Lock:","Blue")
                line = string.replace(line,"Red Lock:","Red")
                line = string.replace(line,"Red/Blue Separation:","Separation")
                line = string.replace(line,"Red/Blue Interval:","Interval")
                line = string.replace(line,"Gravity Corrections","Corrections")
                line = string.replace(line,"Gravity:","Grv:")
                line = string.replace(line,"Number of Sets Collected:","SetsColl")
                line = string.replace(line,"Number of Sets Processed:","SetsProc")
                line = string.replace(line,"Polar Motion:","PolMotC") # This is the PM error, not the values
                line = string.replace(line,"Barometric Pressure:","BarPresCorr")
                line = string.replace(line,"System Setup:","")
                line = string.replace(line,"Total Uncertainty:","Total_unc")
                line = string.replace(line,"Measurement Precision:","Precision")
                line = string.replace(line,":","",1)
                line = string.replace(line,",","")
                line_elements = string.split(line," ")

                # Look for tags
                tags_found = re.search(tags,line)
                Lat_tag_found = re.search(Lat_tag,line)
                Pol_tag_found = re.search(Pol_tag,line)
                Comment_tag_found = re.search(Comment_tag,line)
                Version_tag_found = re.search(Version_tag,line)
                Delta_tag_found = re.search(Delta_tag,line)
                OL_tag_found = re.search(OL_tag,line)
                Grav_tag_found = re.search(Grav_tag,line)
                Unc_tag_found = re.search(Unc_tag,line)
                Grad_tag_found = re.search(Grad_tag,line)
                Rub_tag_found = re.search(Rub_tag,line)
                Name_tag_found = re.search(Name_tag,line)
                Project_tag_found = re.search(Project_tag,line)

                if Unc_tag_found != None:
                    skip_grad = True

                if Grad_tag_found != None:
                    if skip_grad == False:
                        data_array.append(line_elements[1])

                # Old g versions don't output Time Offset, which comes right before gravity
                if Grav_tag_found != None:
                    if version < 5:
                        data_array.append('-999')
                    data_array.append(line_elements[1])

                if Delta_tag_found != None:
                    dtf = True
                    df = " ".join(line_elements[1:])

                if OL_tag_found != None:
                    olf = True
                    of = " ".join(line_elements[1:])

                if Rub_tag_found != None:
                    if dtf == True:
                        data_array.append(df)
                    else:
                        data_array.append('-999')
                    if olf == True:
                        data_array.append(of)
                    else:
                        data_array.append('-999')
                    data_array.append(line_elements[1])

                if Version_tag_found != None:
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

                if tags_found != None:
                    try:
                        data_array.append(line_elements[1])
                    except:
                        data_array.append('-999')

                if Lat_tag_found != None:
                    data_array.append(line_elements[1])
                    data_array.append(line_elements[3])
                    data_array.append(line_elements[5])
                    # This accomodates old versions of g. If these data are to be published,
                    # though, they should be reprocessed in a more recent version.
                    if version < 5:
                        data_array.append('-999') # Setup Height
                        data_array.append('-999') # Transfer Height
                        data_array.append('-999') # Actual Height

                if Pol_tag_found != None:
                    data_array.append(line_elements[1])
                    data_array.append(line_elements[3])
                    # if version < 5:
                    #     data_array.append('-999') # delta factor filename

                if inComments > 0:
                    comments = comments + line
                    if inComments > 1:
                        comments = comments + ' | '
                    inComments += inComments

                if Comment_tag_found != None:
                    inComments = 1
                    comments = ''

            # Old g versions don't output transfer height correction
            if version < 5:
                data_array.append('-999')
            # This adds an Excel formula that looks up the correct polar motion
            data_array.append("=VLOOKUP(S"+`output_line+2`+\
            ",'\\\\Igswzcwwwsjeffk\Shared\Gravity\[finals.data.xlsx]Sheet1'"+\
            "!$F$1:$G$20000,2,FALSE)-L"+`output_line+2`)
            data_array.append("=VLOOKUP(S"+`output_line+2`+\
            ",'\\\\Igswzcwwwsjeffk\Shared\Gravity\[finals.data.xlsx]Sheet1'"+\
            "!$F$1:$I$20000,4,FALSE)-M"+`output_line+2`)
            data_array.append("=VLOOKUP(S"+`output_line+2`+\
            ",'\\\\Igswztwwgszona\Gravity Data Archive\Absolute Data\A-10\Instrument Maintenance"+\
            "\Calibrations\[A10-008 clock and laser calibrations.xlsx]calibrations'!$A$2:$D$20,3,TRUE)-Q"+`output_line+2`)
            data_array.append("=VLOOKUP(S"+`output_line+2`+\
	    ",'\\\\Igswztwwgszona\Gravity Data Archive\Absolute Data\A-10\Instrument Maintenance"+\
            "\Calibrations\[A10-008 clock and laser calibrations.xlsx]calibrations'!$A$2:$D$20,2,TRUE)-P"+`output_line+2`)
            
            data_array.append(comments)

            project_file.close()
            output_line = output_line +1

            # Write data_array to file
            for eachelement in data_array:
                fout.write(eachelement + "\t")
            fout.write('\n')
fout.close()
