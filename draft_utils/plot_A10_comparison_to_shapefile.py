"""
A10 difference-processing script. It takes a data file (created by the Parse_A10 script), looks for measurements at the specificed stations between two date ranges, and calculates the difference. The output is a csv file intended to be merged with a shapefile in Arc for plotting the results. 

Jeff Kennedy, USGS
1/23/2015
"""

from operator import sub
from dateutil import parser

stations = []
data_file = "SanPedro_qaqc.txt"
filesavename = "A10diff.csv"

# Look for measurements between the respective date ranges for each campaign
date1_start = parser.parse("6/1/2014")
date1_end   = parser.parse("6/30/2014")
date2_start = parser.parse("1/1/2015")
date2_end   = parser.parse("1/30/2015")

# Often there's stations in a project folder that we don't want to include in the comparison - instead of using all stations, specify a list of the stations we want.
plot_stations = ["CDF","DORA","EOP","MW3","MW4","MW5","MW6","TW9","MDBLDG","GATE","FIRE","RIST","NEVA"]

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
        
stations = list(set(stations))
        
# Initialize blank array to hold data. First array of each list element is date, second is gravity.
data = [[[],[]]]
for i in range(len(stations)-1):
    data.append([[],[]])

# Compile measured gravity     
with open(data_file) as fp:
    a = fp.readline()
    for line in fp:
        a = line.split("\t")
        sta = a[sta_col]
        sta_index = stations.index(sta)
        # using the dateutil parser we can plot dates directly
        data[sta_index][0].append(parser.parse(a[date_col]))
        data[sta_index][1].append(float(a[grav_col]))

# Setup output array. Bad values are ID'd by -9999. If there's one good and one missing value, a number slightly different than -9999 will be written to ouput.
date1_data = []
date2_data = []
for i in range(len(plot_stations)):
    date1_data.append(-9999)
    date2_data.append(-9999)
    
for idx,station in enumerate(plot_stations):
    if station in stations:
        i = stations.index(station)
        g_dates = (data[i][0])
        for date_idx,g_date in enumerate(g_dates):
            if g_date < date1_end and g_date > date1_start:
                date1_data[idx] = data[i][1][date_idx]
            if g_date < date2_end and g_date > date2_start:
                date2_data[idx] = data[i][1][date_idx]
                    
# Calculate difference and print results
diff = map(sub,date2_data,date1_data)
for s,d in zip(plot_stations,diff):
    print s,d

#write output
fout = open(filesavename,"w")
fout.write("Station,Diff\n")
for i in range(len(diff)):
    string = "%s,%0.2f\n" % (plot_stations[i],diff[i])
    fout.write(string)
fout.close()
