#! python3 
# Plot_A10.py
#
# Takes output file from Parse_A10 (.txt) and generates time-series plots.
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
# NB: Error bars are fixed at +/-10 uGal
#
# Jeff Kennedy, USGS


from numpy import mean
import pylab as plt
from dateutil import parser
from tkinter import filedialog
import math
import matplotlib.dates as mdates
import matplotlib.ticker as tkr
import configparser
import datetime
import sys

config = configparser.ConfigParser()
config.read('X:\\sgp-utils\\sgp-utils\\fg5_plot.ini')

YAXIS_LIMITS_TIGHT = config.getboolean('Parameters', 'YAXIS_LIMITS_TIGHT')
YAXIS_FT_OF_WATER = config.getboolean('Parameters', 'YAXIS_FT_OF_WATER')
ERROR_BAR = float(config.get('Parameters', 'ERROR_BAR'))
SET_XLIM = config.getboolean('Parameters', 'SET_XLIM')
XLEFT = config.get('Parameters', 'XLEFT')
XRIGHT = config.get('Parameters', 'XRIGHT')
# ALTFMT = config.get('Parameters', 'ALTFMT')


# Formats y-axis labels
def func(x, pos):
    s = '{:0,d}'.format(int(x))
    return s


def make_plot(ax, data, station_name, EB):
    myFmt = mdates.DateFormatter('%yy')
    y_format = tkr.FuncFormatter(func)
    ydata = data[1]
    ymean = mean(ydata)
    ydata = [y - ymean for y in ydata]
    ax.errorbar(data[0], ydata, yerr=EB, fmt='kd')
    # ax = plt.gca()
    # Remove scientific notation from axes labels
    # ax.yaxis.get_major_formatter().set_useOffset(False)
    # Add commas to y-axis tick mark labels
    # ax.yaxis.set_major_formatter(y_format)
    # Set x-axis tick labels to just show year

    # Adjust ticks so they fall on Jan 1 and extend past the range of the data. If there
    # are data in January and December, add another year so that there is plenty of space.
    if SET_XLIM:
        ax.set_xlim([XLEFT, XRIGHT])
        # ax.xaxis.set_major_formatter(ALTFMT)
    else:
        ax.xaxis.set_major_formatter(myFmt)
        start_month = data[0][0].month
        start_year = data[0][0].year
        end_month = data[0][-1].month
        end_year = data[0][-1].year
        if start_month == 1:
            start_year = start_year - 1
        if end_month == 12:
            end_year = end_year + 1
        xticks = []
        for iii in range(start_year, end_year + 2):
            xticks.append(datetime.datetime(iii, 1, 1))
        ax.set_xticks(xticks)

    if YAXIS_LIMITS_TIGHT == 'loose':
        max_abs_lim = max(abs(v) for v in ax.get_ylim())
        rounded_abs_lim = math.ceil(max_abs_lim)
        ax.set_ylim([-1 * rounded_abs_lim, rounded_abs_lim])
    if YAXIS_FT_OF_WATER:
        ax.set_ylabel('Storage change,\nin feet of water')
        ax.set_title('{}'.format(station_name))
    else:
        ax.set_ylabel('Gravity change,\nin microGal')
        ax.set_title('{}, mean g={:.1f}'.format(station_name, ymean))


def launch_gui():
    # Open dialog to specify input file. Alternatively, specify file directly.
    data_file = filedialog.askopenfilename(title="Select text file to plot (from A10_parse.py)")
    return data_file


def plot_g(data_file):
    plt.ion()
    stations = []

    # Get station list and column numbers
    with open(data_file) as fp:
        a = fp.readline()
        tags = a.split("\t")
        date_col = tags.index("Date")
        sta_col = tags.index("Station Name")
        grav_col = tags.index("Gravity")
        for line in fp:
            a = line.split("\t")
            stations.append(a[sta_col])
    stations = [s.upper() for s in stations]
    stations = list(set(stations))

    # Initialize blank array to hold data. First array of each list element is date, second is gravity.
    data = [[[], []]]
    for i in range(len(stations)-1):
        data.append([[], []])

    # Get data from input file
    with open(data_file) as fp:
        a = fp.readline()
        for line in fp:
            a = line.split("\t")
            sta = a[sta_col].upper()
            sta_index = stations.index(sta)
            # using the dateutil parser we can plot dates directly
            data[sta_index][0].append(parser.parse(a[date_col]))
            data[sta_index][1].append(float(a[grav_col]))

    if YAXIS_FT_OF_WATER:
        for d in data:
            d[1] = [s/12.77 for s in d[1]]
            eb = ERROR_BAR / 12.77
    else:
        eb = ERROR_BAR

    nfigs = len(data)//4    # floor division: returns integer
    if len(data) % 4 != 0:  # modulo
        nfigs += 1

    for i in range(nfigs):
        plt.figure(figsize=(8.5, 11))
        figidx = i*4
        for ii in range(4):
            if figidx+ii < len(data):
                if data[figidx+ii][0][0]:
                    ax = plt.subplot(4, 1, ii+1)
                    make_plot(ax, data[figidx+ii], stations[figidx+ii], eb)

                    plt.draw()
            plt.show()
            plt.subplots_adjust(bottom=0.25, hspace=0.4, left=0.25, right=0.85)
            # When saved, this exports fonts as fonts instead of paths:
            plt.rcParams['svg.fonttype'] = 'none'
    # This keeps the figure windows open until the user closes them:
    input()


if __name__ == "__main__":
    print(sys.argv)
    if len(sys.argv) == 1:
        data_file = launch_gui()
    else:
        data_file = sys.argv[1]
    plot_g(data_file)
