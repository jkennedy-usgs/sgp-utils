"""get_nwis_data Retrieve groundwater-level data from the USGS National Water Information System.

"""
from dateutil import parser
import requests
import string

def nwis_get_data(cross_ref_file, site_ID):
    """Gets NWIS groundwater-level data via REST API
    
    :param cross_ref_file: csv-separated file with [gravitystation name], [USGS 15-digit ID]
    :param site_ID: gravity station name (e.g., RM109)
    :return: Dictionary with fields 'continuous_x', 'continuous_y', 'discrete_x', and 'discrete 'y'
    """
    with open(cross_ref_file, 'r') as fid:
        for line in fid:
            discrete_x, discrete_y = [], []
            continuous_x, continuous_y = [], []
            out_dic = dict()
            grav_ID, nwis_ID = line.strip().split(',')
            if string.upper(grav_ID) == string.upper(site_ID):
                if len(nwis_ID) == 15:
                    # rdb_meas retrieval is preferred, it returns both discrete and continuous measurements.
                    nwis_URL = 'http://nwis.waterdata.usgs.gov/nwis/dv?cb_72019=on&format=rdb_meas' + \
                               '&site_no=%s' + \
                               '&referred_module=gw&period=&begin_date=1999-10-01&end_date=2018-10-16'
                    r = requests.get(nwis_URL % nwis_ID)
                    # If there is continuous data, it will start with '# ----... WARNING ---...'
                    if r.text[:5] != '# ---':
                    # if no continuous data, retrieve discrete data
                        nwis_URL = 'https://nwis.waterdata.usgs.gov/nwis/gwlevels/?site_no=%s' + \
                                   '&format=rdb_meas'
                        r = requests.get(nwis_URL % nwis_ID)
                    nwis_data = r.text.split('\n')
                    for nwis_line in nwis_data:
                        line_elems = nwis_line.split('\t')
                        # Need to test for null strings because it's possible for there to be a date without a measurement.
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
                    out_dic['continuous_x'] = continuous_x
                    out_dic['continuous_y'] = continuous_y
                    out_dic['discrete_x'] = discrete_x
                    out_dic['discrete_y'] = discrete_y
                    if not out_dic:
                        print('No NWIS data found for site {}'.format(site_ID))
                    return out_dic
                print('Invalid 15-digit ID for site {}'.format(site_ID))
        else:
            print('Gravity Site-ID {} not found in cross-ref file'.format(site_ID))
            return 0
