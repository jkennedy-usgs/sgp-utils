import pandas as pd
from PyQt5.QtWidgets import QMessageBox
DIST_CRITERIA = 0.002
SPEED_CRITERIA = 0.5


class CR_data:
    cosmos_fields = ['RecordNum', 'Date Time(UTC)', 'PTB110_mb', 'P4_mb', 'P1_mb', 'T1_C', 'RH1', 'T_CS215', 'RH_CS215',
                     'Vbat', 'N1Cts', 'N2Cts', 'N1ETsec ', 'N2ETsec ', 'N1T(C)', 'N1RH ', 'N2T(C)', 'N2RH',
                     'GpsUTC', 'LatDec', 'LongDec', 'Alt', 'Qual', 'NumSats', 'HDOP', 'Speed_kmh', 'COG',
                     'SpeedQuality', 'strDate']

    def __init__(self):
        super(CR_data, self).__init__()
        self.df = None
        self.file = None

    def load_data_from_file(self, fname):
        self.file = fname
        exclude_cols = [1, len(self.cosmos_fields)-2]
        data = []
        try:
            fid = open(fname, 'r')
        except IOError:
            QMessageBox.critical(None, 'File error', 'Error opening COSMOS file')
            return False
        else:
            with fid:
                for line in fid:
                    if line[:2] != '//':
                        data_elements = line.split(',')
                        try:
                            d = [float(x.strip()) if idx not in exclude_cols else x for idx, x in enumerate(data_elements)]
                            data.append(d)
                        except:
                            continue

        df = pd.DataFrame(data, columns=self.cosmos_fields)
        df['dist'] = (df['LatDec'].diff() ** 2 + df['LongDec'].diff() ** 2).pow(1. / 2)
        df['dt'] = pd.to_datetime(df['Date Time(UTC)'])
        df['Vbat'] = df['Vbat'].map('{:,.1f}'.format)
        df['LatDec'] = df['LatDec'].map('{:,.5f}'.format)

        self.df = df

    def split_data(self):
        # Criteria:
        #    time > 5 min since last obs
        #    speed ~= 0
        #    dist < 0.005 (should be redundant with first two)
        df = self.df
        data = list()
        durations = list()
        first, last = 1, 1
        for i in range(1, len(self.df)):

            if df['dist'][i] < DIST_CRITERIA and \
                    (df['dt'][i] - df['dt'][i - 1]).seconds == 300:
                # REMOVED:
                # df['Speed_kmh'][i] < SPEED_CRITERIA and \  # Its possible to have two stations separated by less
                # than a 5 minute drive (speed would be 0 for two consecutive log entries)
                last += 1
            else:
                if last - first > 1:
                    data.append(CR_occupation(df[first:last], self.file))
                    durations.append(first - last)
                first, last = i + 1, i + 1
                continue
        return data


class CR_occupation:
    def __init__(self, df, file):
        super(CR_occupation, self).__init__()
        self.df = df
        self.file = file

    @property
    def dtime(self):
        # Return mean observation time
        dt = self.df['dt']
        m = self.df['dt'].min()
        return (m + (dt - m).mean()).to_pydatetime()

    @property
    def duration(self):
        return len(self.df)


if __name__ == '__main__':
    fname = '.\\test_data\\test.dat'
    cr_data = CR_data()
    cr_data.load_data_from_file(fname)
    occupations = cr_data.split_data()
    jeff = 1
