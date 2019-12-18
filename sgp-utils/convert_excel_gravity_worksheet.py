import os
from tkinter import filedialog
from tkinter import *
import pandas as pd
import datetime

# define year of measurements for naming
year = 2019

# Please navigate to folder containing measurement subfolders for specified year
# root = Tk()
# root.withdraw()
# folder = filedialog.askdirectory()

# quick check to see all stations included in that year
folder = "//igswztwwgszona/Gravity Data Archive/Relative Data/All American Canal/2019-05"
for folders in sorted(os.listdir(folder)):
    print(folders)

name_array, time_array, corr_g = [], [], []
user_array, meter_array, date_array = [], [], []

for file in sorted(os.listdir(folder)):
    abs_path = os.path.join(folder + '/' + file)
    if abs_path[-3:] == 'xls' or abs_path[-3:] == 'XLS':

        data_xls = pd.read_excel(abs_path, 'results', index_col=None, usecols=7, dtype='object')
        yr = data_xls['Unnamed: 3'][0]
        dat = datetime.datetime(int(file[0:4]), int(file[4:6]), int(file[6:8]))
        user = data_xls['Unnamed: 2'][3][0]
        meter1 = data_xls['Unnamed: 2'][6]
        meter2 = str(data_xls['Unnamed: 3'][6])
        meter = meter1 + meter2
        xl = pd.ExcelFile(abs_path)
        for sheet in xl.sheet_names:
            if sheet not in ['results', 'tide', 'metertable'] \
                    and sheet.find('Sheet') == -1 \
                    and sheet.find('sheet') == -1:
                print(sheet)

                sheet_data = pd.read_excel(abs_path, sheet, index_col=False)
                ctr = 1.0
                for i in range(sheet_data.shape[0]):
                    if type(sheet_data.iloc[i, 1]) == datetime.time and not pd.isna(sheet_data.iloc[i, 10]):
                        time_array.append(datetime.datetime.combine(dat, sheet_data.iloc[i, 1]))
                        corr_g.append(sheet_data.iloc[i, 10]/1000)
                        name_array.append(sheet)
                        user_array.append(user)
                        meter_array.append(meter)

data_tuples = list(zip(name_array, user_array, meter_array, time_array, corr_g))
df = pd.DataFrame(data_tuples, columns=['name', 'user', 'meter', 'date', 'corr_g']).sort_values(by=['date'])
df['time'] = df['date'].dt.strftime('%H:%M:%S')
addl_cols = ['col5', 'col6', 'col7', 'col8', 'col9', 'col10', 'col11', 'col12', 'col3', 'col4']
for i in range(len(addl_cols)):
    df[addl_cols[i]] = 0
df.to_csv('aac_test.txt',
          date_format='%Y/%m/%d',
          sep=' ', header=False,
          index=False,
          float_format='%.4f',
          columns=['name', 'user', 'meter', 'date', 'time','corr_g'] + addl_cols)
