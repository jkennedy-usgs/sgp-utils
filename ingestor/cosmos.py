import pandas as pd
import datetime as dt

DIST_CRITERIA = 0.005
SPEED_CRITERIA = 0.5

class CR_data:
    cosmos_fields = ['RecordNum', 'Date Time(UTC)', 'PTB110_mb', 'P4_mb', 'P1_mb', 'T1_C', 'RH1', 'T_CS215', 'RH_CS215',
                     'Vbat', 'N1Cts', 'N2Cts', 'N1ETsec ', 'N2ETsec ', 'N1T(C)', 'N1RH ', 'N2T(C)', 'N2RH',
                     'GpsUTC', 'LatDec', 'LongDec', 'Alt', 'Qual', 'NumSats', 'HDOP', 'Speed_kmh', 'COG',
                     'SpeedQuality', 'strDate']

    def __init__(self):
        super(CR_data, self).__init__()
        self.df = None

    def load_data_from_file(self, fname):
        df = pd.read_csv(fname, comment='/', names=self.cosmos_fields)
        df['dist'] = (df['LatDec'].diff()**2 + df['LongDec'].diff()**2).pow(1./2)
        df['dt'] = pd.to_datetime(df['Date Time(UTC)'])
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
        for i in range(1,len(self.df)):

            if df['dist'][i] < DIST_CRITERIA and \
              df['Speed_kmh'][i] < SPEED_CRITERIA and \
              (df['dt'][i] - df['dt'][i-1]).seconds == 300:
                 last +=1
            else:
                if last - first > 1:
                    data.append(CR_occupation(df[first:last]))
                    durations.append(first-last)
                first, last = i+1, i+1
                continue
        return data

class CR_occupation:
    def __init__(self, df):
        super(CR_occupation, self).__init__()
        self.df = df

    @property
    def dtime(self):
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