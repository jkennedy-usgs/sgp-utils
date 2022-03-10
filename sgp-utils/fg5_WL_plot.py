#!/usr/bin/python3
# fg5_WL_plot.py
#
# Plots gravity and groundwater level time series. Groundwater levels are retrieved automatically from NWIS via
# REST API.
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
# Jeff Kennedy, USGS

from numpy import mod, ceil
import matplotlib.pylab as plt
from dateutil import parser
import datetime
from tkinter import filedialog
from tkinter import Tk
import matplotlib.dates as mdates
import matplotlib.ticker as tkr
from nwis import nwis_get_data

# Parameters and default values:
a10_sd = 5				              # Default A-10 standard deviation, for error bars
convert_to_water = True			      # Converts gravity change to thickness-of-water change (41.9 microGal/m)
consistent_date_axes = True		      # Causes all plots to have the same time span (set by x_min, x_max)
cross_ref_file = 'SiteIDcrossref.csv' # File with gravity station names and corresponding 15-digit USGS ID
figs_per_page = 4			          # plots per page
meters = True				          # Use meters or feet

# specify x-axis limits, instead of taking them from the data. If only gravity data are present (no water levels), the
# date range will be taken from the gravity data.
if consistent_date_axes:
    x_min = datetime.datetime(2009,1,1)
    x_max = datetime.datetime(2021,1,1)


# Formats y-axis labels
def func(x, pos):
    s = '{}'.format(x)
    return s

# Value to subtract from observed gravity so the plotted values are reasonable
offset = 978990000

# Open dialog to specify input file. Alternatively, specify file directly.
data_file = filedialog.askopenfilename(title="Select text file to plot (from A10_parse.py)")
# data_file = "SanPedro_qaqc.txt"

# Matplotlib interactive mode
plt.ioff()
stations = []
myFmt = mdates.DateFormatter('%Y')
y_format = tkr.FuncFormatter(func)

# Get station list and column numbers
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
stations = list(set(stations))

# Initialize blank array to hold data. First array of each list element is date, second is gravity.
grav_data = [[[], []]]
nwis_data = ['']*len(stations)
for i in range(len(stations)-1):
    grav_data.append([[], []])

for station in stations:
    sta_index = stations.index(station)
    nwis_data[sta_index] = (nwis_get_data(cross_ref_file, station))

# Get gravity data from input file
with open(data_file) as fp:
    a = fp.readline()
    for line in fp:
        a = line.split("\t")
        sta = a[sta_col]
        sta_index = stations.index(sta)
        # using the dateutil parser we can plot dates directly
        grav_data[sta_index][0].append(parser.parse(a[date_col]))
        grav_data[sta_index][1].append(float(a[grav_col]) - offset)

figidx = 1
i = 0
plt.figure(figsize=(8.5, 11))
while i < len(grav_data):
    if nwis_data[i]:
        if figidx >= (figs_per_page + 1):
            plt.figure(figsize=(8.5, 11))
            figidx = 1
        plt.subplot(4,1,figidx)
        grav_x = grav_data[i][0]
        grav_y = grav_data[i][1]
        ytemp = []
        y0 = grav_y[0]

        if convert_to_water:
            if meters:
                ytemp = [(p-y0) / 41.9 for p in grav_y]
                a10sd = a10_sd / 41.9
            else:
                ytemp = [(p-y0) / 12.77 for p in grav_y]
                a10sd = a10_sd / 12.77
            rng = max(ytemp) - min(ytemp)
            half_rng = ceil(rng)
        else:
            ytemp = [(p-y0) for p in grav_y]
            a10sd = a10_sd
        grav_y = ytemp
        plt.errorbar(grav_x, grav_y, yerr=a10sd, fmt='kd')

        ax = plt.gca()
        #if convert_to_water:
        #    ax.set_ylim(0-half_rng, 0+half_rng)
        ax2 = ax.twinx()

        if nwis_data[i]['continuous_x']:
            nwis_x = nwis_data[i]['continuous_x']
            nwis_y = nwis_data[i]['continuous_y']
        else:
            nwis_x = nwis_data[i]['discrete_x']
            nwis_y = nwis_data[i]['discrete_y']

        if meters:  # NWIS default is feet
            nwis_y = [meas * .3048 for meas in nwis_y]
        ax2.plot(nwis_x, nwis_y)
        ax2.invert_yaxis()


        # Remove scientific notation from axes labels
        # ax.yaxis.get_major_formatter().set_useOffset(False)

        # Add commas to y-axis tick mark labels
        ax.yaxis.set_major_formatter(y_format)
        # Set x-axis tick labels to just show year
        ax.xaxis.set_major_formatter(myFmt)

        if not consistent_date_axes:
            # Adjust ticks so they fall on Jan 1 and extend past the range of the data. If there
            # are data in January and December, add another year so that there is plenty of space.
            start_month = grav_data[i][0][0].month
            start_year = grav_data[i][0][0].year
            end_month = grav_data[i][0][-1].month
            end_year = grav_data[i][0][-1].year
            if start_month == 1:
                start_year = start_year-1
            if end_month == 12:
                end_year = end_year + 1
            xticks = []
            for iii in range(start_year,end_year+2):
                xticks.append(datetime.datetime(iii,1,1))
            ax.set_xticks(xticks)
        else:
            ax.set_xlim(x_min, x_max)
        if convert_to_water:
            if meters:
                ax.set_ylabel('Storage change,\nin m of water')
            else:
                ax.set_ylabel('Storage change,\nin ft of water')
        else:
            ax.set_ylabel('Gravity change,\nin microGal')
        if meters:
            ax2.set_ylabel('Depth to\ngroundwater, m')
        else:
            ax2.set_ylabel('Depth to\ngroundwater, ft')
        plt.title(stations[i])
        plt.draw()

        plt.subplots_adjust(bottom=0.25, hspace=0.4, left=0.25, right=0.85)
        # When saved, this exports fonts as fonts instead of paths:
        plt.rcParams['svg.fonttype'] = 'none'
        figidx += 1
    i += 1

plt.show()