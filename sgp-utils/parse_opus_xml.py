"""
Script to parse OPUS XML

"""
import re
import os
import sys
import tkinter
from tkinter import filedialog
from tkinter import Tk
from time import strftime

#import tkFileDialog
import xml.etree.ElementTree as ET
import string
import os

deg_fields = ['DEGREES', 'MINUTES', 'SECONDS']
coord_fields = ['LAT', 'EAST_LONG']

root = tkinter.Tk()
root.withdraw()
data_directory = os.getcwd()

# data_directory = filedialog.askdirectory(
#     parent=root,initialdir=pd)
# a = data_directory.split('/')
# data_directory = "E:\\Shared\\current\\python\\opus"


def launch_gui():
    root = Tk()
    root.withdraw()
    files = filedialog.askopenfilenames(
        parent=root, 
        initialdir=os.getcwd(),
        filetypes=[('xml','.xml')]
        )
    return files

def parse_directory(data_directory):
    files = []
    for dirname, dirnames, filenames in os.walk(data_directory):
        for filename in filenames:
            if filename[-4:] == '.xml':
                files.append(os.path.join(dirname, filename).replace('"',''))
    return files


def parse_files(files, file):
    with open(file, "w+") as fid:
        fid.write("File,Date,Datum,Latitude,Longitude,Ellipsoid height,")
        fid.write("Orthometric height,Easting,Northing,")
        fid.write("x uncertainty,y uncertainty,z uncertainty\n")
        for file in files:
            line1 = parse_file(file)
            fid.write(line1 + '\n')


def parse_file(fname):
    line = fname[:-4] + ','
    tree = ET.parse(fname)
    rt = tree.getroot()
    elem = rt.find('{https://www.ngs.noaa.gov/OPUS/schema/1.0}OBSERVATION_TIME')
    line += elem.get('START') + ','

    elem = rt.find('{https://www.ngs.noaa.gov/OPUS/schema/1.0}POSITION')
    line += elem.find('{https://www.ngs.noaa.gov/OPUS/schema/1.0}REF_FRAME').text + ','

    cs = elem.find('{https://www.ngs.noaa.gov/OPUS/schema/1.0}COORD_SET')
    ec = cs.find('{https://www.ngs.noaa.gov/OPUS/schema/1.0}ELLIP_COORD')
    for cf in coord_fields:
        lat = ec.find('{https://www.ngs.noaa.gov/OPUS/schema/1.0}' + cf)
        coord = []
        for df in deg_fields:
            coord.append(
                lat.find('{https://www.ngs.noaa.gov/OPUS/schema/1.0}' + df).text)
        c = float(coord[0]) + float(coord[1]) / 60. + float(coord[2]) / 3600.
        if cf == 'EAST_LONG':
            c -= 360.
        line += f'{c:.6f}' + ','
    eh = float(ec.find('{https://www.ngs.noaa.gov/OPUS/schema/1.0}EL_HEIGHT').text)
    oh = float(rt.find('{https://www.ngs.noaa.gov/OPUS/schema/1.0}ORTHO_HGT').text)
    line += f'{eh:.3f},{oh:.3f},'
    
    utm = rt.find('{https://www.ngs.noaa.gov/OPUS/schema/1.0}PLANE_COORD_INFO')
    pcs = utm.find('{https://www.ngs.noaa.gov/OPUS/schema/1.0}PLANE_COORD_SPEC')
    utm_east = float(pcs.find('{https://www.ngs.noaa.gov/OPUS/schema/1.0}EASTING').text)
    utm_north = float(pcs.find('{https://www.ngs.noaa.gov/OPUS/schema/1.0}NORTHING').text)
    line += f'{utm_east:.3f},{utm_north:.3f},'
    
    rc = cs.find('{https://www.ngs.noaa.gov/OPUS/schema/1.0}RECT_COORD')
    for i in rc.findall('{https://www.ngs.noaa.gov/OPUS/schema/1.0}COORDINATE'):
        if i.attrib["AXIS"] == "X":
            x_unc = i.attrib["UNCERTAINTY"]
        elif i.attrib["AXIS"] == "Y":
            y_unc = i.attrib["UNCERTAINTY"]
        elif i.attrib["AXIS"] == "Z":
            z_unc = i.attrib["UNCERTAINTY"]
    line += f'{x_unc},{y_unc},{z_unc}'
    return line
    
def get_filesavename(data_directory):
    return os.path.join(data_directory, f'OPUS_results_{strftime("%Y-%m-%d-%H%M")}.csv')    

if __name__ == "__main__":
    if len(sys.argv) == 1:
        files = launch_gui()
    else:
        files = []
        print(sys.argv)
        with open(sys.argv[1], "r") as fid:
            files = fid.read().splitlines()
    data_directory = os.path.dirname(files[0].replace('"',''))
    print(data_directory)
    filesavename = get_filesavename(data_directory)
    parse_files(files, filesavename)