#! python3 
# A10_SY_plot.py
#
# Creates specific yield plots (change in thickness of free-standing water vs. groundwater-level change).
#
# User is prompted for a file with gravity data. This tab-delimited file needs to have a one line header, and
# include the columns:
#
#     Date  |  Station Name  |  Gravity
#
# A file with the appropriate format is created by A10_parse.py. Alternatively, the file can be created by hand as
# long as it has the above columns (in any order, and with or without additional columns).
#
# Groundwater levels corresponding to gravity measurements are retrieved from NWIS. A file (cross_ref_file) serves as a
# lookup table between gravity station IDs and NWIS 15-digit IDs. If there is a gw level within a certain period of time
# (threshold), that level is assigned to the gravity measurement. Otherwise, if there are no gw levels within
# (threshold), the program will check the length of the gap between the previous gw level (relative to the gravity
# measurement) and the next gw level. If this time period is less than (interpolate_threshold), the gw level at the
# will be time of the gravity measurement will be linearly interpolated.
#
# Plots are not automatically saved. They can be saved by using the save
# button in the figure window, or by
#
# plt.savefig('\path\to\savefile.svg')
#
# SVG format imports correctly into Illustrator. If using a different format,
# one might need to change the line at the end ('plt.rcParams(...)') to a
# different file type.
#
# Parameters and default values:
#   presentation_style = False             If true, plot font size is increased
#   cross_ref_file = 'SiteIDcrossref.csv'  File with gravity station names and corresponding 15-digit USGS ID
#   threshold = 5                          days - if a gw level is this close to a gravity measurement, they correspond.
#   interpolate_threshold = 50             If the total gap between the gw level prior to the gravity meas, and the gw
#                                          level after the measurement, is less than this, linearly interpolate the gw
#                                          level at the time of the gravity measurement.
#
#
#  Jeff Kennedy, USGS


import numpy as np
import pylab as plt
import datetime
from tkinter import filedialog
from tkinter import Tk
import matplotlib.dates as mdates
import matplotlib.ticker as tkr
import csv
import os
from nwis import nwis_get_data
from dateutil import parser

# # When saved, this exports fonts as fonts instead of paths:
plt.rcParams['svg.fonttype'] = 'none'
plt.interactive(False)
# Parameters than can be changed
presentation_style = True  # Makes labels big
cross_ref_file = 'SiteIDcrossref.csv'
threshold = datetime.timedelta(days=5)  # If within a threshold, just take the nearest data point
interpolate_threshold = datetime.timedelta(days = 50)  # otherwise, interpolate if the data gap is below a threshold
write_output_to_file = True

# Formats y-axis labels
def func(x, pos):
    s = '{:0,d}'.format(int(x))
    return s

def write_to_file(filesavename, station, g_date, g, gwl, code, gap, y1, y2):
    with open(filesavename, 'a') as fn:
        fn.write('{},{},{},{},{},{},{},{}\n'.format(station, g_date, g, gwl, code, gap, y1, y2))

# Open dialog to specify input file. Alternatively, specify file directly.
root = Tk()
root.withdraw()
data_file = filedialog.askopenfilename(title="Select text file to plot (from A10_parse.py)")

if write_output_to_file:
    out_file = data_file[:-4]
    filesavename = str.replace(str(data_file), '.txt', '_SY.csv')
    with open(filesavename, 'w+') as fn:
        fn.write('Station,date,g,gwl,type,gap,start,end\n')
# data_file = "SanPedro_qaqc.txt"

# Matplotlibn interactive mode
plt.ion()
stations = []
myFmt = mdates.DateFormatter('%Y')
y_format = tkr.FuncFormatter(func)

# Get station list and column numbers from input file header
with open(data_file) as fp:
    a = fp.readline()
    a = a.strip()
    tags = a.split("\t")
    date_col = tags.index("Date")
    sta_col = tags.index("Station Name")
    grav_col = tags.index("Gravity")
    for line in fp:
        a = line.split("\t")
        stations.append(a[sta_col])
# Remove duplicates
stations = list(set(stations))

# Initialize blank array to hold data. First array of each list element is date, second is gravity.
grav_data = [[[], []]]
nwis_data = ['']*len(stations)
for i in range(len(stations)-1):
    grav_data.append([[], []])

# Retrieve data from nwis (will return both discrete and continuous data)
for station in stations:
    sta_index = stations.index(station)
    nwis_data[sta_index] = (nwis_get_data(cross_ref_file, station))
    if nwis_data[sta_index] != 0:
        nwis_data[sta_index]['station'] = station

# Get gravity data from input file
with open(data_file) as fp:
    a = fp.readline()
    for line in fp:
        a = line.split("\t")
        sta = a[sta_col]
        sta_index = stations.index(sta)
        # using the dateutil parser we can plot dates directly
        grav_data[sta_index][0].append(parser.parse(a[date_col]))
        grav_data[sta_index][1].append(float(a[grav_col]))

for idx, sta in enumerate(nwis_data):
    if sta != 0:  # Could be blank station names?
        if sta['continuous_x'] or sta['discrete_x']:  # Make sure there's some data
            plot_x, plot_y = [], []
            min_delta_cont, min_delta_disc = datetime.timedelta(days=1000000), datetime.timedelta(days=1000000)
            # Iterate through the gravity values for a given station
            for g_idx, g_date in enumerate(grav_data[idx][0]):
                # find closest continuous data
                if sta['continuous_x']:
                    repdate = np.repeat(g_date, len(sta['continuous_x']))    # vector of gravity-meas. dates
                    delta_cont = np.asarray(sta['continuous_x']) - repdate   # vector of time-deltas
                    min_delta_cont = min(np.absolute(delta_cont))
                    idx_cont = np.argmin(np.absolute(delta_cont))     # index of gw level closest to gravity meas
                # and closest discrete data
                if sta['discrete_x']:
                    repdate = np.repeat(g_date, len(sta['discrete_x']))
                    delta_disc = np.asarray(sta['discrete_x']) - repdate
                    min_delta_disc = min(np.absolute(delta_disc))
                    idx_disc = np.argmin(np.absolute(delta_disc))
                # check threshold
                if min_delta_cont < threshold or min_delta_disc < threshold:
                    if min_delta_cont < min_delta_disc:
                        plot_x.append(sta['continuous_y'][idx_cont])
                        plot_y.append(grav_data[idx][1][g_idx])
                        write_to_file(filesavename, sta['station'], g_date, plot_y[-1], plot_x[-1], 'C', min_delta_cont.days, '0', '0')
                    elif min_delta_cont > min_delta_disc:
                        plot_x.append(sta['discrete_y'][idx_disc])
                        plot_y.append(grav_data[idx][1][g_idx])
                        write_to_file(filesavename, sta['station'], g_date, plot_y[-1], plot_x[-1], 'D', min_delta_disc.days, '0', '0')
                    continue
                else: # No water-level measurements are very close. Check if we can interpolate.
                    interpolate = False
                    x1, x2, y1, y2 = [], [], [], []
                    cont_gap, disc_gap = datetime.timedelta(days=1000000), datetime.timedelta(days=1000000)
                    if sta['continuous_x']:  # calculate continuous gap
                        if any(i < datetime.timedelta(days=0) for i in delta_cont) and \
                                any(i > datetime.timedelta(days=0) for i in delta_cont): # Check if data on both sides of gap
                            closest_neg = max([i for i in delta_cont if i <= datetime.timedelta(days=0)]) # time delta to closest negative diff
                            closest_pos = min([i for i in delta_cont if i >= datetime.timedelta(days=0)])
                            idx_closest_neg_cont, = np.nonzero(delta_cont == closest_neg)[0]
                            idx_closest_pos_cont, = np.nonzero(delta_cont == closest_pos)[0]
                            cont_gap = np.absolute(closest_neg) + closest_pos
                    if sta['discrete_x']:
                        if any(i < datetime.timedelta(days=0) for i in delta_disc) and \
                                any(i > datetime.timedelta(days=0) for i in delta_disc):  # Check if data on both sides of gap
                            closest_neg = max([i for i in delta_disc if i <= datetime.timedelta(days=0)]) # time delta to closest negative diff
                            closest_pos = min([i for i in delta_disc if i >= datetime.timedelta(days=0)])
                            idx_closest_neg_disc, = np.nonzero(delta_disc == closest_neg)[0]
                            idx_closest_pos_disc, = np.nonzero(delta_disc == closest_pos)[0]
                            disc_gap = np.absolute(closest_neg) + closest_pos
                    if cont_gap < disc_gap: # interpolate the data type with the smaller gap
                        if cont_gap < interpolate_threshold:
                            x1 = sta['continuous_x'][idx_closest_neg_cont]
                            x2 = sta['continuous_x'][idx_closest_pos_cont]
                            y1 = sta['continuous_y'][idx_closest_neg_cont]
                            y2 = sta['continuous_y'][idx_closest_pos_cont]
                            interpolate = True
                            gap = cont_gap
                    elif disc_gap < cont_gap:
                        if disc_gap < interpolate_threshold:
                            x1 = sta['discrete_x'][idx_closest_neg_disc]
                            x2 = sta['discrete_x'][idx_closest_pos_disc]
                            y1 = sta['discrete_y'][idx_closest_neg_disc]
                            y2 = sta['discrete_y'][idx_closest_pos_disc]
                            interpolate = True
                            gap = disc_gap
                    if interpolate:
                        x1 = x1.toordinal()
                        x2 = x2.toordinal()
                        poly = np.polyfit([x1, x2], [y1, y2], 1)
                        p = np.poly1d(poly)
                        interpolated_dtw= p(g_date.toordinal())
                        plot_x.append(interpolated_dtw)
                        plot_y.append(grav_data[idx][1][g_idx])
                        print('Interpolated DTW at station {}, measurement on {}'.format(sta['station'], g_date))

                        print('Time gap = {}, WL change {} feet.'.format(gap, y2 - y1))
                        if write_output_to_file:
                            write_to_file(filesavename, sta['station'], g_date, plot_y[-1], plot_x[-1], 'I', gap.days, y1, y2)
                    else:
                        if write_output_to_file:
                            write_to_file(filesavename, sta['station'], g_date, grav_data[idx][1][g_idx], '0', 'N', '0', '0', '0')
                        print('no valid data to interpolate at station {}, measurement on {}'.format(sta['station'], g_date))

            if len(plot_y) > 1: # If there's only 1 data point, don't bother
                if presentation_style:
                    font = {'family': 'normal',
                            'weight': 'bold',
                            'size': 16}
                    plt.rc('font', **font)
                    plt.subplots_adjust(bottom=0.15, top=0.85, hspace=0.4, left=0.25, right=0.85)
                plot_y = [(y-plot_y[0])/41.9 for y in plot_y]
                plot_x = [(x-plot_x[0])*-.3048 for x in plot_x]
                try:  # Sometimes polyfit fails, even if there's 3 points?
                    poly, cov = np.polyfit(plot_x, plot_y, 1, cov=True)
                    cc = np.corrcoef(plot_x, plot_y)[0,1]
                    line_x = np.linspace(min(plot_x)-0.2, max(plot_x)+0.2,10)
                    p = np.poly1d(poly)
                    line_y = p(line_x)
                    plt.figure(facecolor='white')
                    plt.plot(plot_x, plot_y,'.')
                    plt.plot(line_x,line_y)
                    plt.title(sta['station'])
                    ax = plt.gca()
                    plt.ylabel('Change in water storage\n(meters of free-standing water, from gravity data)')
                    plt.xlabel('Change in groundwater level (meters)')
                    plt.figtext(0.25, 0.85, 'Sy = %0.2f ± %0.02f' % (poly[0], np.sqrt(cov[0,0])))
                    plt.figtext(0.25, 0.81, 'r^2 = %0.2f' % cc)
                    plt.savefig(sta['station'] + '.svg')
                    plt.show()
                except ValueError as e:
                    print(e)


# This keeps the figure windows open until the user closes them:
# input()


