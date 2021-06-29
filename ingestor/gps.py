import os
import subprocess
import georinex as gr
import datetime

# For naming Rinex files
alphabet = 'abcdefghijklmnopqrstuvwx'

def convert_T01_to_dat(fullfile):
    os.system('runpkr00.exe -d "{}"'.format(fullfile))

def convert_dat_to_rinex(fullfile):
    os.system('teqc.exe -tr d "{}" > "{}"'.format(fullfile.replace('T01', 'dat'),
                                              fullfile.replace('T01', 'rnx')))


class GPS_data:
    def __init__(self, rinex_file):
        self._hdr = gr.rinexheader(rinex_file)
        self.times = gr.gettime(rinex_file)
        self.file = rinex_file
        self.T01_file = rinex_file.replace('rnx', 'T01')
        self.rinex_filename = ''

    @property
    def duration(self):
        # Just need a measure of duration for comparison, not the actual duration
        return len(self.times)

    @property
    def doy(self):
        result = subprocess.check_output('teqc +quiet +mds +doy "{}"'.format(self.file))
        year_day = result.decode().split()[0]
        doy = year_day.split(':')[1]
        return doy

    @property
    def hour(self):
        return int(self._hdr['TIME OF FIRST OBS'].split()[3])

    @property
    def year(self):
        return self.dtime.strftime('%Y')

    @property
    def month(self):
        return self.dtime.strftime('%m')

    @property
    def hour_as_letter(self):
        return alphabet[self.hour]

    @property
    def dtime(self):
        # Return mean observation time
        avgTime = datetime.datetime.fromtimestamp(sum(map(datetime.datetime.timestamp, self.times)) / len(self.times))
        return avgTime

    @property
    def year_suffix(self):
        return '.' + self.dtime.strftime('%y') + 'o'

    def update_rinex_filename(self, stationname):
        if len(stationname) >= 4:
            sn = stationname[:4]
        else:
            sn = stationname + 'x' * 4 - (len(stationname))
        self.rinex_filename = sn + self.doy + self.hour_as_letter + self.year_suffix
