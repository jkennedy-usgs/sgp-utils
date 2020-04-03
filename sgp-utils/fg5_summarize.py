""""
Script to parse A10 files and create a text file with the basic info needed in
the field. Intended for the printing of data sheets for a field binder

Should work with g8 and g9.

Jeff Kennedy
USGS
"""

import string
import re
import os
from tkinter import filedialog
from tkinter import Tk
from time import strftime

gravity_data_archive = "X:\\Absolute Data\\A-10"

root = Tk()
root.withdraw()
data_directory = filedialog.askdirectory(
    parent=root, initialdir=gravity_data_archive)

# data_directory = r'X:/Absolute Data/A-10/Working Data/Imperial Valley'

print(data_directory)
output_line=0

#open file for overwrite (change to "r" to append)
# Dummy file to close later
fout = open('temp.txt',"w")

#write data descriptor file header

# Going to assume that project files are stored in subdirectories of a site directory
old_site = ''
for dirname,dirnames,filenames in os.walk(data_directory):
    if 'unpublished' in dirnames:
        dirnames.remove('unpublished')
    for filename in filenames:
        fname = os.path.join(dirname, filename)
        # If the file name ends in "project.txt"
        if str.find(fname,'project.txt') != -1:
            project_file = open(fname)
            print(fname)
            data_descriptor = 0
            data_list = ['']*7
            # Look for these words in the g file
            tags = re.compile(r'Name|Setht|Date|Gravity|Scatter|SetsColl|SetsProc')
            inComments = 0
            Comment_tag = re.compile(r'Comments')
            for line in project_file:
                # Change up some text in the g file to make it easier to parse
                # (remove duplicates, etc.)
                line = str.strip(line)
                line = str.replace(line,'\n\n','\n')
                line = str.replace(line,":  ",": ")
                # Repeat to take care of ":   " (three spaces)
                line = str.replace(line,":  ",": ")
                line = str.replace(line,":  ",": ")
                line = str.replace(line,"Gravity Data Archive","GDA")
                line = str.replace(line,"Project Name:","Project")
                line = str.replace(line,"File Created:","Created")
                line = str.replace(line,"Setup Height:","Setht")
                line = str.replace(line,"Delta Factor Filename:","DFFile")
                line = str.replace(line,"Ocean Load ON, Filename:","OLFile")
                line = str.replace(line," Height:","")
                line = str.replace(line,"Nominal Air Pressure:","Nominal")
                line = str.replace(line,"Barometric Admittance Factor:","Admittance")
                line = str.replace(line," Motion Coord:","")
                line = str.replace(line,"Set Scatter:","Scatter")
                line = str.replace(line,"Offset:","ofst")
                line = str.replace(line,"Time Offset (D h:m:s):","Offset")
                line = str.replace(line,"Ocean Load:","OLC")
                line = str.replace(line,"Rubidium Frequency:","RubFrequency")
                line = str.replace(line,"Blue Lock:","Blue")
                line = str.replace(line,"Red Lock:","Red")
                line = str.replace(line,"Red/Blue Separation:","Separation")
                line = str.replace(line,"Red/Blue Interval:","Interval")
                line = str.replace(line,"Gravity Corrections","Corrections")
                line = str.replace(line,"Number of Sets Collected:","SetsColl")
                line = str.replace(line,"Number of Sets Processed:","SetsProc")
                line = str.replace(line,"Polar Motion:","PolMotC") # This is the PM error, not the values
                line = str.replace(line,"Barometric Pressure:","")
                line = str.replace(line,"System Setup:","")
                line = str.replace(line,"Total Uncertainty:","Total_unc")
                line = str.replace(line,"Measurement Precision:","Precision")
                line = str.replace(line,":","")
                line = str.replace(line,",","")
                line_elements = str.split(line," ")

                # Look for tags
                tags_found = re.search(tags,line)
                Comment_tag_found = re.search(Comment_tag,line)

                if tags_found != None:
                    data_list[data_descriptor] = line_elements[1]
                    data_descriptor = data_descriptor + 1

                if inComments > 0:
                    comments = comments + line
                    if inComments > 1:
                        comments = comments + ' | '
                    inComments += inComments

                if Comment_tag_found != None:
                    inComments = 1
                    comments = ''

            site = data_list[0]
            comments = comments.strip()
            if len(comments) > 1:
                if comments[-1] == '|':
                    comments = comments[:-1]

            data_list.append(comments)
            if site != old_site:
                fout.close()
                old_site = site
                filesavename = os.getcwd()  + '/' + site + '.txt'
                fout = open(filesavename,"w")
                fout.write('Station: ' + site + '\n\n')
                fout.write('Date\t     Setup Hgt\tGravity\t      Scatter SetsColl SetsProc\n')
            for idx, eachelement in enumerate(data_list):
                if idx == len(data_list) - 1:
                    fout.write('\n')
                if idx == 0:
                    bl = ''
                elif idx == 1:
                    fout.write(data_list[2] + '\t')
                elif idx == 2:
                    fout.write(data_list[1] + '\t')

                else:
                    fout.write(eachelement + "\t")
            fout.write('\n\n')

            project_file.close()
fout.close()
