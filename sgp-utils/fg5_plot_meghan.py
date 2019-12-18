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


from numpy import mod
import pylab as plt
from dateutil import parser
import datetime
import tkFileDialog
import math
import matplotlib.dates as mdates
import matplotlib.ticker as tkr

YAXIS_LIMITS = 'tight' #loose'  # 'tight' or 'loose'
YAXIS_FT_OF_WATER = True #True or False
ERROR_BAR = 10  # microGal
XLIM = None  #[parser.parse('2018-02-01'),parser.parse('2018-05-25')]  # Uses default values if not defined
altFmt = mdates.DateFormatter('%y')  # Only used if XLIM is not None

# Formats y-axis labels
def func(x, pos):
    s = '{:0,d}'.format(int(x))
    return s

# Value to subtract from observed gravity so the plotted values are reasonable
offset = 978990000

# Open dialog to specify input file. Alternatively, specify file directly.
#Tkinter.Tk().withdraw() # Close the root window
data_file = tkFileDialog.askopenfilename(title="Select text file to plot (from A10_parse.py)")
# data_file = "SanPedro_qaqc.txt"

plt.ion()
stations = []
myFmt = mdates.DateFormatter('%y')
y_format = tkr.FuncFormatter(func)

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
data = [[[],[]]]
for i in range(len(stations)-1):
    data.append([[],[]])

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
        data[sta_index][1].append(float(a[grav_col])-offset)

offset_data = []
offset_datum = []
for d in data:
    first_datum = d[1][0]
    out_g = [s - first_datum for s in d[1]]
    if YAXIS_FT_OF_WATER:
        out_g = [s/12.77 for s in out_g]
        ERROR_BAR /= 12.77
    out_d = [s for s in d[0]]
    offset_data.append([out_d, out_g])

data = offset_data

#print len(data)
nfigs = len(data)/4
if mod(len(data),4) != 0:
    nfigs+=1

#print nfigs, 4 plots per page
for i in range(nfigs):
    plt.figure(figsize=(8.5,11))
    figidx = i*4
    for ii in range(4):  
        if figidx+ii < len(data):
            if data[figidx+ii][0][0]:
                plt.subplot(4,1,ii+1)
                plt.errorbar(data[figidx+ii][0], data[figidx+ii][1], yerr=ERROR_BAR, fmt='kd')
                ax = plt.gca()
        # Remove scientific notation from axes labels
                # ax.yaxis.get_major_formatter().set_useOffset(False)
        # Add commas to y-axis tick mark labels
                # ax.yaxis.set_major_formatter(y_format)
        # Set x-axis tick labels to just show year
               

        # Adjust ticks so they fall on Jan 1 and extend past the range of the data. If there
        # are data in January and December, add another year so that there is plenty of space.
                if XLIM:
                    ax.set_xlim(XLIM)
                    ax.xaxis.set_major_formatter(altFmt)
                else:
                    ax.xaxis.set_major_formatter(myFmt)
                    start_month = data[figidx+ii][0][0].month
                    start_year = data[figidx+ii][0][0].year
                    end_month = data[figidx+ii][0][-1].month
                    end_year = data[figidx+ii][0][-1].year
                    if start_month == 1:
                        start_year = start_year-1
                    if end_month == 12:
                        end_year = end_year + 1
                    xticks = []
                    for iii in range(start_year,end_year+2):
                        xticks.append(datetime.datetime(iii,1,1))
                    ax.set_xticks(xticks)
                plt.title(stations[figidx+ii])
                if YAXIS_LIMITS == 'loose':
                    max_abs_lim = max(abs(v) for v in ax.get_ylim())
                    rounded_abs_lim = math.ceil(max_abs_lim)
                    ax.set_ylim([-1*rounded_abs_lim,rounded_abs_lim])
                if YAXIS_FT_OF_WATER:
                    plt.ylabel('Storage change,\nin feet of water')
                else:
                    plt.ylabel('Gravity change,\n in microGal')

                plt.draw()
                
        plt.subplots_adjust(bottom=0.25, hspace=0.4, left=0.25, right=0.85)

# When saved, this exports fonts as fonts instead of paths:
        plt.rcParams['svg.fonttype'] = 'none'
# This keeps the figure windows open until the user closes them:
raw_input()
