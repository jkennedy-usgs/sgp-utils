"""get_nwis_data Retrieve groundwater-level data from the USGS National Water Information System.

"""
from dateutil import parser
import requests
import matplotlib.pyplot as plt
import datetime
import string

def plot_wells(cross_ref_file, site_IDs):
    fig, ax = plt.subplots()
    for well in site_IDs:
        well_data = nwis_get_data(cross_ref_file, well)

        if well_data['continuous_x']:
            ydata_meters = [x * 0.3048 for x in well_data['continuous_y']]
            ax.plot(well_data['continuous_x'], ydata_meters, label=well, linewidth=0.5)
        else:
            ydata_meters = [x * 0.3048 for x in well_data['discrete_y']]
            ax.plot(well_data['discrete_x'], ydata_meters, label=well, linewidth=0.5)
    ax.invert_yaxis()
    ax.set_ylabel("Depth to groundwater (meters)", fontname="Times New Roman", fontsize=12)
    for tick in ax.get_xticklabels():
        tick.set_fontname("Times New Roman")
    for tick in ax.get_yticklabels():
        tick.set_fontname("Times New Roman")
    L = plt.legend()
    plt.setp(L.texts, family='Times New Roman')
    plt.xlim([datetime.datetime(2006,1,1,0,0,0), datetime.datetime(2019,1,1,0,0,0)])
    plt.show()
    input()
    

def nwis_get_data(cross_ref_file, gravity_station_ID):
    """Gets NWIS groundwater-level data via REST API
    
    :param cross_ref_file: csv-separated file with [gravitystation name], [USGS 15-digit ID]
    :param gravity_station_ID: gravity station name (e.g., RM109)
    :return: Dictionary with fields 'continuous_x', 'continuous_y', 'discrete_x', and 'discrete 'y'
    """
    if gravity_station_ID.isnumeric() and len(gravity_station_ID) == 15:
        nwis_ID = gravity_station_ID
        grav_ID = gravity_station_ID
    else:
        with open(cross_ref_file, 'r') as fid:
            for line in fid:

                grav_ID, nwis_ID = line.strip().split(',')
                if grav_ID.upper() == gravity_station_ID.upper():
                    if len(nwis_ID) != 15:
                        print('Invalid 15-digit ID for site {}'.format(gravity_station_ID))
                        return 0
                    else:
                        break
            else:
                print('Gravity Site-ID {} not found in cross-ref file'.format(gravity_station_ID))
                return 0

    discrete_x, discrete_y = [], []
    continuous_x, continuous_y = [], []
    out_dic = dict()
    # rdb_meas retrieval is preferred, it returns both discrete and continuous measurements.
    nwis_URL = 'http://nwis.waterdata.usgs.gov/nwis/dv?cb_72019=on&format=rdb_meas' + \
               f'&site_no={nwis_ID}' + \
               '&referred_module=gw&period=&begin_date=1999-10-01&end_date=2021-03-01'
    print('Retrieving rdb data for {} from {}'.format(grav_ID, nwis_URL))
    r = requests.get(nwis_URL)
    # If there is continuous data, it will start with '# ----... WARNING ---...'
    if r.text[:5] != '# ---':
    # if no continuous data, retrieve discrete data
        nwis_URL: str = f'https://nwis.waterdata.usgs.gov/nwis/gwlevels/?site_no={nwis_ID}' + \
                   '&format=rdb_meas'
        print('No continuous data for {}. Retrieving discrete data from {}'.format(grav_ID, nwis_URL))
        r = requests.get(nwis_URL)
    nwis_data = r.text.split('\n')
    for nwis_line in nwis_data:
        line_elems = nwis_line.split('\t')
        # Need to test for null strings because it's possible for there to be a date without a measurement.
        try:  # the rdb format has changed; parsing by '\t' barely works with the fixed-width fields
            if line_elems[0] == u'USGS':
                if line_elems[2] == u'GW':
                    if line_elems[6] != u'':
                        discrete_x.append(parser.parse(line_elems[3]))
                        discrete_y.append(float(line_elems[6]))
                elif line_elems[3] != u'':
                    discrete_x.append(parser.parse(line_elems[2]))
                    discrete_y.append(float(line_elems[6]))
                elif line_elems[4] != u'':
                    continuous_x.append(parser.parse(line_elems[2]))
                    continuous_y.append(float(line_elems[4]))
        except Exception as e:
            continue
    out_dic['continuous_x'] = continuous_x
    out_dic['continuous_y'] = continuous_y
    out_dic['discrete_x'] = discrete_x
    out_dic['discrete_y'] = discrete_y
    if not out_dic:
        print('No NWIS data found for site {}'.format(gravity_station_ID))
    return out_dic



if __name__ == "__main__":
    plot_wells('SiteIDcrossref.csv', ['T2-S2','AAC-17','PK-1','T1-S5','324421114482101'])