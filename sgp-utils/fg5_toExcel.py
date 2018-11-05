""""
Script to convert fg5_parse output to an Excel file.

The script works on project.txt files in a specified directory (and subdirectories). The output file name is the same
as the input file name with an .xlsx extension.
Written for Python 2.7

Jeff Kennedy
USGS
"""

import string
import os
import tkFileDialog
import datetime
import pandas as pd
from time import strftime
import string
import xlsxwriter
from dateutil import parser
from nwis_get_data import nwis_get_data

# User-specified options

# Either use a specified file, or show a GUI for the user to decide
data_file = tkFileDialog.askopenfilename(title="Select text file to plot (from A10_parse.py)")
#data_file = u"\\\\Igswztwwgszona\\Gravity Data Archive\\Absolute Data\\A-10\\Final Data\\Big Chino\\Big Chino_Final_20180108-1331_noDriftCorrection.txt"

# If true, set the axis limits consistent for all axes
CONSISTENT_Y_AXES = True
Y_AXES_LIMITS = [-100, 100]

# Import water-level data from NWIS
IMPORT_WLS = True
cross_ref_file = "SiteIDcrossref.csv"

output_file = string.split(data_file,'\\')[-1]
output_file = string.replace(output_file, '.txt', '.xlsx')
workbook = xlsxwriter.Workbook(output_file)
format = workbook.add_format({'num_format': 'yyyy-mm-dd'})

stations = []
# Get station list and column numbers
with open(data_file) as fp:
    a = fp.readline()
    tags = a.split("\t")
    date_col = tags.index("Date")
    sta_col = tags.index("Station Name")
    grav_col = tags.index("Gravity")
    unc_col = tags.index("Set Scatter")

    for line in fp:
        a = line.split("\t")
        stations.append(a[sta_col])
stations = [s.upper() for s in stations]
stations = list(set(stations))

# Initialize blank array to hold data. First array of each list element is date, second is gravity.
data = [[[], [], []]]
for i in range(len(stations) - 1):
    data.append([[], [], []])

# Get data from input file
with open(data_file) as fp:
    a = fp.readline()
    for line in fp:
        a = line.split("\t")
        sta = a[sta_col].upper()
        print sta
        sta_index = stations.index(sta)
        # using the dateutil parser we can plot dates directly
        data[sta_index][0].append(parser.parse(a[date_col]))
        data[sta_index][1].append(float(a[grav_col]))
        data[sta_index][2].append(float(a[unc_col]))

offset_data = []
offset_datum = []

# Add another column to the data array with gravity relative to first observation
for d in data:
    first_datum = d[1][0]
    out_g = [s - first_datum for s in d[1]]
    out_d = [s for s in d[0]]
    offset_data.append([out_d, d[1], out_g, d[2]])

data = offset_data

for idx1, station_data in enumerate(data):
    worksheet = workbook.add_worksheet(stations[idx1])
    worksheet_idx = 1
    worksheet.write_row(0,0,["Date",
                             "g",
                             "relative dg",
                             "Uncertainty",
                             "relative dH2O",
                             "relative GWL",
                             "GWL",
                             "relative dH2O unc.",
                             "NWIS discrete",
                             "NWIS discrete GWL",
                             "NWIS cont",
                             "NWIS cont GWL"])
    for idx2, d in enumerate(station_data[0]):
        worksheet.write(worksheet_idx, 0, station_data[0][idx2], format)
        worksheet.write(worksheet_idx, 1, station_data[1][idx2])
        worksheet.write(worksheet_idx, 2, station_data[2][idx2])
        worksheet.write(worksheet_idx, 3, station_data[3][idx2])
        worksheet.write(worksheet_idx, 4, station_data[2][idx2]/42)
        # Leave a blank column to fill in relative GWL change - too variable to do here, must
        # be done by hand
        # Lookup dicscrete GWL based on date; convert to m and elevation
        # (Depth BLS is retrieved from NWIS)
        worksheet.write(worksheet_idx, 6, '=VLOOKUP(A'
                        + str(worksheet_idx+1)
                        + ', I1:J100, 2, FALSE) * -0.3048')
        worksheet.write(worksheet_idx, 7, station_data[2][idx2]/42)
        worksheet_idx += 1

    # Set column width
    worksheet.set_column('A:G', 16)

    # import WLs from NWIS
    if IMPORT_WLS:
        print "importing from NWIS:" + stations[idx1]
        nwis_data = (get_nwis_data(cross_ref_file, stations[idx1]))

        if nwis_data != 0:
            # Truncate tape-down times so VlOOKUP works correctly
            nwis_data['discrete_x'] = [i.date() for i in nwis_data['discrete_x']]
            worksheet.write_column("I2", nwis_data['discrete_x'], format)
            worksheet.write_column("J2", nwis_data['discrete_y'])
            worksheet.write_column("K2", nwis_data['continuous_x'], format)
            worksheet.write_column("L2", nwis_data['continuous_y'])

    # Time series chart
    chart_ts = workbook.add_chart({'type': 'scatter'})
    chart_ts.add_series({
        'name': 'Gravity change at ' + stations[idx1],
        'categories': [stations[idx1], 1, 0, worksheet_idx, 0],
        'values': [stations[idx1], 1, 2, worksheet_idx, 2],
        'marker': {'type': 'diamond'},
        'y_error_bars': {
            'type': 'fixed',
            'value': 10}})
    chart_ts.set_legend({'none': True})
    worksheet.insert_chart('A30', chart_ts, {'x_offset': 25, 'y_offset': 10})

    # Specific yield plot
    chart_sy = workbook.add_chart({'type': 'scatter'})
    chart_sy.add_series({
        'name': 'Specific yield at ' + stations[idx1],
        'categories': [stations[idx1], 1, 5, 20, 5],
        'values': [stations[idx1], 1, 4, 20, 4],
        'marker': {'type': 'diamond'}})
    chart_sy.set_legend({'none': True})
    worksheet.insert_chart('G30', chart_sy, {'x_offset': 25, 'y_offset': 10})

    if CONSISTENT_Y_AXES:
        chart_ts.set_y_axis({'min': Y_AXES_LIMITS[0],
                          'max': Y_AXES_LIMITS[1],
                          'crossing': Y_AXES_LIMITS[0]})
        chart_ts.set_x_axis({'min': 39814,
                          'max': 43101,
                          'date_axis': True,
                          'num_format': 'yyyy',
                             })


workbook.close()
