#! python3 
# -*- coding: utf8 -*-
"""
This software was developed by the U.S. Geological Survey Southwest Gravity Program.
See: https://github.com/jkennedy-usgs/ingestor for current project source code

Written for Python 3 and PyQt5

Contact: Jeff Kennedy, jkennedy@usgs.gov

License:            Creative Commons Attribution 4.0 International (CC BY 4.0)
                    http://creativecommons.org/licenses/by/4.0/
PURPOSE
------------------------------------------------------------------------------
Ingestor is a program to copy, subdivide, and rename files collected as part of
routine absolute-gravity data collection. Based on a date range and user-specified
directories, the program:

1) Looks for .project.txt files in laptop_gdata_backup collected between the
specified dates and copies these and the accompanying files (*.fg5, *.gsf) to the
Working Data directory

2) Splits a COSMOS-probe text file into occupations that match up with .project.txt
files (based on the time of the measurement), and copies these to the measurement
directory in Working Data.

3) Looks for photos that match the g measurement time, renames them with the site
name, and copies them to the Site Descriptions directory.

4) Looks for fieldsheets that match the g measurement time, copies them to the
measurement directory in Working Data.

The last directories (i.e., the text strings in the boxes on the main dialog are
stored in a Qsettings object, they will be restored each time the program is launched.


U.S. GEOLOGICAL SURVEY DISCLAIMER
------------------------------------------------------------------------------
This software has been approved for release by the U.S. Geological Survey
(USGS). Although the software has been subjected to rigorous review,
the USGS reserves the right to update the software as needed pursuant to
further analysis and review. No warranty, expressed or implied, is made by
the USGS or the U.S. Government as to the functionality of the software and
related material nor shall the fact of release constitute any such warranty.
Furthermore, the software is released on condition that neither the USGS nor
the U.S. Government shall be held liable for any damages resulting from
its authorized or unauthorized use.
Any use of trade, product or firm names is for descriptive purposes only and
does not imply endorsement by the U.S. Geological Survey.
Although this information product, for the most part, is in the public domain,
it also contains copyrighted material as noted in the text. Permission to
reproduce copyrighted items for other than personal use must be secured from
the copyright owner.
------------------------------------------------------------------------------
"""
import os
import re
import sys
import glob
import exifread
import datetime
import webbrowser  # opens .txt and .csv files in system viewer
from shutil import copy, copyfile
import configparser

from fg5 import FG5
from cosmos import CR_data
import gps

from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog, QTableWidgetItem, QWidget, QMessageBox, QFileDialog
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QFont, QIcon
from PyQt5.QtCore import QDateTime, QSettings, QSize, Qt
from PyQt5 import uic

try:
    Ui_MainWindow, MainWindowBase = uic.loadUiType(r'ui\ingestor.ui')
    Ui_PreviewWindow, PreviewWindowBase = uic.loadUiType(r'ui\preview.ui')
    Ui_Calendar, CalendarWindowBase = uic.loadUiType(r'ui\calendar.ui')
except:
    Ui_MainWindow, MainWindowBase = uic.loadUiType(r'ingestor.ui')
    Ui_PreviewWindow, PreviewWindowBase = uic.loadUiType(r'preview.ui')
    Ui_Calendar, CalendarWindowBase = uic.loadUiType(r'calendar.ui')

G_CR_TIME_DIFF_THRESHOLD = 25 * 60  # in seconds
G_PHOTO_TIME_DIFF_THRESHOLD = 30 * 60
PICTURE_SIZE = 200  # For preview, in pixels

START_DATE_OFFSET = -60  # in days before present to start looking for project files

alphabet = 'abcdefghijklmnopqrstuvwxyz'  # For sequential photo renaming

COPY_G, PARSE_COSMOS, COPY_PHOTOS, COPY_FIELDSHEETS, COPY_GPS = range(5)  # Items in main dialog

# Write this to the start of each COSMOS file
cosmos_header = \
    '//Hydroinnova CRS Probe Filename: 1808191350.txt\n' + \
    '//****Provide the full data file, with the header information, if support is needed.\n' + \
    '//Logger FWVer = 4.009, 2015/04/29, Rover FW, 16 NPMs\n' + \
    '//Logger SerialNum=16100706\n' + \
    '//Probe BootType = 5\n' + \
    '//NumberOfNPMs= 2\n' + \
    '//NPM#01: SerialNum=17110123, FWVer=205, HV=1500,G=2.40,D=18,UT=62, DeadTime=500, RemoteLEDMode=1, NBins=64\n' + \
    '//NPM#02: SerialNum=17110126, FWVer=205, HV=1500,G=2.30,D=19,UT=62, DeadTime=500, RemoteLEDMode=1, NBins=64\n\n' + \
    '//Recordperiod = 5 minutes.\n' + \
    '//DataSelect=r1p4p1t1h1t7h7bn1n2e1e2s1s2\n' + \
    '//--Data Column Info:\n' + \
    '//RecordNum,Date Time(UTC),PTB110_mb,P4_mb,P1_mb,T1_C,RH1,T_CS215,RH_CS215,Vbat,N1Cts,N2Cts, N1ETsec , N2ETsec , N1T(C),N1RH , N2T(C),N2RH ,\n' + \
    '//GpsUTC, LatDec, LongDec, Alt, Qual, NumSats, HDOP, COG, Speed_kmh, SpeedQuality, strDate\n'

config = configparser.ConfigParser()
config.read('ingestor.ini')
site_description_directory = config.get('Parameters', 'SITE_DESCRIPTION_DIRECTORY')
archive_gps_directory  = config.get('Parameters', 'GPS_DIRECTORY')

class MyApp(QMainWindow):

    def __init__(self):
        super(MyApp, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.preview_window = Preview(self)
        self.calendar = Calendar()

        self.settings = QSettings('SGP', 'INGESTOR')
        self.init_fields()
        self.update_fields()
        self.settings.sync()

        self.calendar.ui.calendarWidget.clicked.connect(self.set_date)
        self.ui.endDateEdit.setDate(QDateTime.currentDateTime().date())
        self.ui.startDateEdit.setDate(QDateTime.currentDateTime().date().addDays(START_DATE_OFFSET))

        # List of fg5 objects
        self.g_data = None
        # Flag for calendar display
        self.setting_start_date = None
        self.setWindowIcon(QIcon(r'ui\icon.png'))

    def init_fields(self):
        """
        If it's the first time a user has opened ingestor, populate the directories/files

        :return: None
        """
        if self.settings.value('g_test_dir') is None:
            self.settings.setValue('g_test_dir',
                                   '\\\\Igswztwwgszona\\Gravity Data Archive\\')
        if self.settings.value('g_input_dir') is None:
            self.settings.setValue('g_input_dir',
                                   '\\\\Igswztwwgszona\\Gravity Data Archive\\Absolute Data\\A-10\\Laptop_gdata_backup')
        if self.settings.value('cosmos_dir') is None:
            self.settings.setValue('cosmos_dir',
                                   '\\\\Igswztwwgszona\\Gravity Data Archive\\')
        if self.settings.value('photo_dir') is None:
            self.settings.setValue('photo_dir',
                                   '\\\\Igswztwwgszona\\Gravity Data Archive\\')
        if self.settings.value('fieldsheet_dir') is None:
            self.settings.setValue('fieldsheet_dir',
                                   '\\\\Igswztwwgszona\\Gravity Data Archive\\')
        if self.settings.value('gps_dir') is None:
            self.settings.setValue('gps_dir',
                                   '\\\\Igswztwwgszona\\Gravity Data Archive\\')

    def update_fields(self):
        """
        Set text fields in main window

        :return: None
        """
        self.ui.gLineEdit.setText(self.settings.value('g_input_dir'))
        self.ui.photoLineEdit.setText(self.settings.value('photo_dir'))
        self.ui.cosmosLineEdit.setText(self.settings.value('cosmos_dir'))
        self.ui.fieldsheetLineEdit.setText(self.settings.value('fieldsheet_dir'))
        self.ui.GPSLineEdit.setText(self.settings.value('gps_dir'))

    def show_date_start(self):
        self.setting_start_date = True
        self.calendar.setWindowTitle('Find files after...')
        self.calendar.show()

    def show_date_end(self):
        self.setting_start_date = False
        self.calendar.setWindowTitle('Find files before...')
        self.calendar.show()

    def set_date(self, date):
        if self.setting_start_date:
            if date < self.ui.endDateEdit.date():
                self.ui.startDateEdit.setDate(date)
        else:
            if date > self.ui.startDateEdit.date():
                self.ui.endDateEdit.setDate(date)
        self.calendar.hide()

    def update_settings_from_textboxes(self):
        """
        After starting copying process, store the textbox directories/files in Qsettings object
        :return:
        """
        textboxes = [self.ui.gLineEdit,
                     self.ui.cosmosLineEdit,
                     self.ui.photoLineEdit,
                     self.ui.fieldsheetLineEdit,
                     self.ui.GPSLineEdit]
        settings = ['g_input_dir',
                    'cosmos_dir',
                    'photo_dir',
                    'fieldsheet_dir',
                    'gps_dir']
        for idx, textbox in enumerate(textboxes):
            self.settings.setValue(settings[idx], textbox.text())

    def ingest(self):
        """
        Called when "OK" button is clicked in the initial window.
        :return:
        """
        if self.ui.startDateEdit.date() > self.ui.endDateEdit.date():
            MessageBox('Please choose an end date later than the start date.', '')
            return
        self.update_settings_from_textboxes()
        self.study_area = os.path.basename(self.settings.value('g_input_dir'))
        self.g_data = self.get_g_data(self.settings.value('g_input_dir'))
        if self.ui.listWidget.item(COPY_G).checkState():
            self.populate_preview_table_with_g_files(self.g_data)
        else:
            self.populate_preview_table_with_g_files(self.g_data, check=False)

        if self.ui.listWidget.item(PARSE_COSMOS).checkState():
            cr_occupations = self.get_CR_occupations(self.settings.value('cosmos_dir'))
            if not cr_occupations:
                return
            self.sync_cr_with_g(cr_occupations)
            self.populate_preview_table_with_CR_occupations(self.g_data)

        if self.ui.listWidget.item(COPY_PHOTOS).checkState():
            self.sync_photos_with_g(self.settings.value('photo_dir'))
            self.populate_preview_table_with_photos(self.g_data)

        if self.ui.listWidget.item(COPY_FIELDSHEETS).checkState():
            self.sync_fieldsheet_with_g(self.settings.value('fieldsheet_dir'))
            self.populate_preview_table_with_fieldsheets(self.g_data)

        if self.ui.listWidget.item(COPY_GPS).checkState():
            gps_occupations = self.get_GPS_occupations(self.settings.value('gps_dir'))
            self.sync_GPS_with_g(gps_occupations)
            self.populate_preview_table_with_GPS_occupations(self.g_data)

        self.preview_window.ui.previewTableWidget.resizeColumnsToContents()
        self.preview_window.ui.previewTableWidget.resizeRowsToContents()

        self.ui.progressBar.setValue(0)
        self.ui.progressBar.update()

        self.preview_window.exec_()

    def sync_cr_with_g(self, cr_occupations):
        """
        Matches up cosmic-ray occupation with gravity observation, based on time stamps
        :param cr_occupations: List of CR_occupation objects (from cosmos.py)
        :return: None
        """
        self.ui.statusbar.showMessage('Finding COSMOS occupations...')
        self.ui.statusbar.update()
        self.ui.progressBar.setRange(0, len(self.g_data))
        self.ui.progressBar.setValue(0)
        self.ui.progressBar.update()
        i = 0
        for g_occ in self.g_data:
            match_list = list()
            i += 1
            self.ui.progressBar.setValue(i)
            self.ui.progressBar.update()
            for cr_occ in cr_occupations:
                if abs(g_occ.dtime - cr_occ.dtime) < datetime.timedelta(0, G_CR_TIME_DIFF_THRESHOLD):
                    match_list.append(cr_occ)
            if len(match_list) > 0:
                if len(match_list) > 1:
                    cr_occ_dur = [cr_occ.duration for cr_occ in match_list]
                    best_cr_idx = max(range(len(cr_occ_dur)), key=cr_occ_dur.__getitem__)
                    g_occ.cr_occ = match_list[best_cr_idx]
                else:
                    g_occ.cr_occ = match_list[0]
                self.ui.statusbar.showMessage('')
        self.ui.statusbar.update()

    def sync_GPS_with_g(self, gps_occupations):

        i = 0
        for g_occ in self.g_data:
            self.ui.statusbar.showMessage('')
            self.ui.statusbar.update()
            match_list = list()
            i += 1
            self.ui.progressBar.setValue(i)
            self.ui.progressBar.update()
            for gps_occ in gps_occupations:
                if abs(g_occ.dtime - gps_occ.dtime) < datetime.timedelta(0, G_CR_TIME_DIFF_THRESHOLD):
                    match_list.append(gps_occ)
            if len(match_list) > 0:
                if len(match_list) > 1:
                    gps_occ_dur = [gps_occ.duration for gps_occ in match_list]
                    best_gps_idx = max(range(len(gps_occ_dur)), key=gps_occ_dur.__getitem__)
                    best_gps_occ = match_list[best_gps_idx]
                    best_gps_occ.update_rinex_filename(g_occ.stationname)
                    g_occ.gps_occ = best_gps_occ
                else:
                    best_gps_occ = match_list[0]
                    best_gps_occ.update_rinex_filename(g_occ.stationname)
                    g_occ.gps_occ = best_gps_occ
                self.ui.statusbar.showMessage('')
        self.ui.statusbar.update()

    def sync_fieldsheet_with_g(self, fs_dir):
        self.ui.statusbar.showMessage('Analyzing fieldsheets...')
        self.ui.statusbar.update()
        fs_dict = dict()
        for filename in os.listdir(fs_dir):
            if filename.find('.pdf') != -1:
                try:
                    temp_filename = filename.replace('.pdf', '')
                    filename_elems = temp_filename.split('_')
                    if len(filename_elems) > 2:  # '' in station name
                        station_name = filename_elems[0]
                        for i in range(len(filename_elems) - 2):
                            station_name += '_' + filename_elems[i + 1]
                    else:
                        station_name = filename_elems[0]
                    date_elems = filename_elems[-1].split('-')
                    year, month, day = int(date_elems[0]), int(date_elems[1]), int(date_elems[2])
                    fs_date = datetime.datetime(year, month, day, 12, 0, 0)
                    if self.ui.startDateEdit.date() < fs_date < self.ui.endDateEdit.date():
                        fs_dict[(station_name, year, month, day)] = os.path.join(fs_dir, filename)
                except:
                    MessageBox('Error reading fieldsheet PDF: {}'.format(filename),
                               'Is it in the format <station name>_YYYY-MM-DD?')

        for g_occ in self.g_data:
            try:
                g_occ.fs_from_path = fs_dict[g_occ.tuple_key]
                to_path = g_occ.filename.replace('Laptop_gdata_backup', 'Working Data')
                g_occ.fs_to_path = os.path.join(os.path.dirname(to_path), os.path.basename(g_occ.fs_from_path))
            except:
                g_occ.fs_from_path = 'Could not find field sheet: {} {}'.format(g_occ.stationname, g_occ.date)
                g_occ.fs_to_path = 'NA'
                continue

    def sync_photos_with_g(self, photo_dir):
        self.ui.statusbar.showMessage('Finding photos...')
        self.ui.statusbar.update()
        i = 0

        photo_dic = dict()
        for dirname, _, filenames in os.walk(photo_dir):
            self.ui.progressBar.setRange(0, len(filenames))
            self.ui.progressBar.setValue(0)
            self.ui.progressBar.update()

            for filename in filenames:
                if filename[-4:].upper() == '.JPG':
                    with open(os.path.join(dirname, filename), 'rb') as fh:
                        i += 1
                        self.ui.progressBar.setValue(i)
                        self.ui.progressBar.update()
                        tags = exifread.process_file(fh, stop_tag="EXIF DateTimeOriginal")
                        if not tags:
                            text1 = 'EXIF date tag not found in photo: ' + filename
                            MessageBox(text1, 'File not processed.')
                        date_taken = tags["EXIF DateTimeOriginal"]
                        date_and_time = str(date_taken).split(' ')
                        date = date_and_time[0].split(':')
                        time = date_and_time[1].split(':')
                        photo_orig_dt = datetime.datetime(int(date[0]), int(date[1]), int(date[2]),
                                                          int(time[0]),
                                                          int(time[1]), int(time[2]))
                        photo_dt = photo_orig_dt - datetime.timedelta(hours=int(self.ui.timeSpinBox.value()))
                    photo_dic[photo_dt] = os.path.join(dirname, filename)
        for g_occ in self.g_data:
            matched_photos = list()
            i += 1
            self.ui.progressBar.setValue(i)
            self.ui.progressBar.update()
            for k, v in photo_dic.items():
                if abs(g_occ.dtime - k) < datetime.timedelta(0, G_PHOTO_TIME_DIFF_THRESHOLD):
                    matched_photos.append(v)
            g_occ.photos = matched_photos
            self.ui.statusbar.showMessage('')
        self.ui.statusbar.update()

    def get_GPS_occupations(self, dirname):
        gps_occupations = []
        for filename in os.listdir(dirname):
            if filename[-3:] == 'T01':
                self.ui.statusbar.showMessage('Converting Trimble .T01 to rinex: {}'.format(filename))
                self.ui.statusbar.update()
                fullfile = os.path.join(dirname, filename)
                try:
                    gps.convert_T01_to_dat(fullfile)
                    gps.convert_dat_to_rinex(fullfile)
                    gps_occ = gps.GPS_data(fullfile.replace('T01', 'rnx'))
                    gps_occupations.append(gps_occ)
                except:
                    MessageBox('Error reading/converting GPS data: {}'.format(filename))
                    continue
        return gps_occupations

    def get_CR_occupations(self, dirname):
        cr_dfs = []
        for filename in os.listdir(dirname):
            if filename[-3:] == 'RVR' or filename[-3:] == 'txt':
                try:
                    cr_data = CR_data()  # cr_data: all data from 1 .RVR file
                    cr_data.load_data_from_file(os.path.join(dirname, filename))
                    cr_dfs.append(cr_data)
                except:
                    MessageBox('Error reading Cosmos data: {}'.format(filename))
                    continue
        if len(cr_dfs) > 0:
            cr_out = []  # cr_out: list of CR_occupations
            for df in cr_dfs:
                cr_out += df.split_data()
        else:
            MessageBox('no Cosmos data found.', '')
            return False

        return cr_out

    def populate_preview_table_with_photos(self, data):
        self.ui.statusbar.showMessage('Adding photos to preview...')
        self.ui.statusbar.update()
        i = 0
        self.ui.progressBar.setRange(0, len(data))
        self.ui.progressBar.setValue(0)
        self.ui.progressBar.update()
        for fg5 in data:
            i += 1
            self.ui.progressBar.setValue(i)
            self.ui.progressBar.update()
            if fg5.photos:
                for idx, photo_complete_path in enumerate(fg5.photos):
                    row = self.insert_checkbox_and_row()
                    image_widget = ImgWidget(photo_complete_path)
                    proj_dir = os.path.dirname(os.path.dirname(os.path.dirname(fg5.filename)))
                    site_dir = os.path.dirname(os.path.dirname(fg5.filename))
                    self.preview_window.ui.previewTableWidget.setItem(row, 1, QTableWidgetItem('Copy and rename photo'))
                    self.preview_window.ui.previewTableWidget.setItem(row, 2, QTableWidgetItem(photo_complete_path))
                    photo_file = os.path.join(site_description_directory, os.path.basename(proj_dir),
                                              os.path.basename(site_dir),
                                              fg5.stationname + '_' +
                                              fg5.dtime.strftime('%Y-%m-%d') +
                                              alphabet[idx] + '.jpg')
                    self.preview_window.ui.previewTableWidget.setItem(row, 3,
                                                                      QTableWidgetItem(photo_file))
                    self.preview_window.ui.previewTableWidget.setCellWidget(row, 4, image_widget)
                    self.preview_window.ui.previewTableWidget.setRowHeight(row, 200)
                    if os.path.isfile(photo_file):
                        self.preview_window.ui.previewTableWidget.item(row, 3).setBackground(QColor(Qt.red))
                        self.preview_window.ui.previewTableWidget.repaint()
                self.ui.statusbar.showMessage('')
        self.ui.statusbar.update()

    def populate_preview_table_with_GPS_occupations(self, data):
        for fg5 in data:
            if fg5.gps_occ:
                row = self.insert_checkbox_and_row()
                description = QTableWidgetItem('Copy and convert GPS occupation, station '
                                               + fg5.stationname
                                               + ' '
                                               + fg5.date)
                date_dir = fg5.gps_occ.year + '-' + fg5.gps_occ.month
                gps_to_path = os.path.join(archive_gps_directory, self.study_area, date_dir, fg5.gps_occ.rinex_filename)
                item = self.preview_item()
                description.gps_occ = fg5.gps_occ
                self.preview_window.ui.previewTableWidget.setItem(row, 1, description)
                self.preview_window.ui.previewTableWidget.setItem(row, 2, QTableWidgetItem(fg5.gps_occ.T01_file))
                self.preview_window.ui.previewTableWidget.setItem(row, 3, QTableWidgetItem(gps_to_path))
                self.preview_window.ui.previewTableWidget.setItem(row, 4, item)
                if os.path.exists(gps_to_path):
                    self.preview_window.ui.previewTableWidget.item(row, 3).setBackground(QColor(Qt.red))
                    self.preview_window.ui.previewTableWidget.repaint()

    def populate_preview_table_with_CR_occupations(self, data):
        for fg5 in data:
            if fg5.cr_occ:
                row = self.insert_checkbox_and_row()
                description = QTableWidgetItem('Copy CR occupation, station '
                                               + fg5.stationname
                                               + ', '
                                               + fg5.date)
                cr_to_path = os.path.join(fg5.to_dir, fg5.stationname + '_CR_' + fg5.dtime.strftime('%Y-%m-%d') +
                                          '.txt')
                item = self.preview_item()
                description.cr_occ = fg5.cr_occ
                self.preview_window.ui.previewTableWidget.setItem(row, 1, description)
                self.preview_window.ui.previewTableWidget.setItem(row, 2, QTableWidgetItem(fg5.cr_occ.file))
                self.preview_window.ui.previewTableWidget.setItem(row, 3, QTableWidgetItem(cr_to_path))
                self.preview_window.ui.previewTableWidget.setItem(row, 4, item)
                if os.path.exists(cr_to_path):
                    self.preview_window.ui.previewTableWidget.item(row, 3).setBackground(QColor(Qt.red))
                    self.preview_window.ui.previewTableWidget.repaint()

    def populate_preview_table_with_g_files(self, data, check=True):
        for fg5 in data:
            from_full_path = fg5.filename
            to_path = fg5.filename.replace('Laptop_gdata_backup', 'Working Data')
            fg5.from_dir = os.path.dirname(from_full_path)
            fg5.to_dir = os.path.dirname(to_path)
            if check:
                row = self.insert_checkbox_and_row(check)
                text = QTableWidgetItem('Copy ' +
                                        os.path.basename(fg5.filename) +
                                        ' (' +
                                        fg5.collected +
                                        ' sets)')
                self.preview_window.ui.previewTableWidget.setItem(row, 1, text)

                self.preview_window.ui.previewTableWidget.setItem(row, 2, QTableWidgetItem(from_full_path))
                self.preview_window.ui.previewTableWidget.setItem(row, 3, QTableWidgetItem(to_path))
                item = self.preview_item()
                self.preview_window.ui.previewTableWidget.setItem(row, 4, item)
                if os.path.exists(to_path):
                    self.preview_window.ui.previewTableWidget.item(row, 3).setBackground(QColor(Qt.red))
                    self.preview_window.ui.previewTableWidget.repaint()

    def preview_item(self):
        item = QTableWidgetItem('Preview')
        item.setText('Preview')
        item.setForeground(QBrush(QColor(0, 0, 255)))
        link_font = QFont(item.font())
        link_font.setUnderline(True)
        item.setFont(link_font)
        item.setTextAlignment(Qt.AlignHCenter)
        return item

    def populate_preview_table_with_fieldsheets(self, data):
        for fg5 in data:
            row = self.insert_checkbox_and_row()
            text = QTableWidgetItem('Copy fieldsheet')
            item = self.preview_item()
            self.preview_window.ui.previewTableWidget.setItem(row, 1, text)
            self.preview_window.ui.previewTableWidget.setItem(row, 2, QTableWidgetItem(fg5.fs_from_path))
            self.preview_window.ui.previewTableWidget.setItem(row, 3, QTableWidgetItem(fg5.fs_to_path))
            self.preview_window.ui.previewTableWidget.setItem(row, 4, item)
            if 'Could not find' in fg5.fs_from_path:
                self.preview_window.ui.previewTableWidget.item(row, 0).setCheckState(0)

    def insert_checkbox_and_row(self, check=True):
        row = self.preview_window.ui.previewTableWidget.rowCount()
        self.preview_window.ui.previewTableWidget.insertRow(row)
        cb = QTableWidgetItem('')
        if check:
            cb.setCheckState(2)
        else:
            cb.setCheckState(0)
        self.preview_window.ui.previewTableWidget.setItem(row, 0, cb)
        return row

    def get_g_data(self, g_dir):
        data = list()
        self.ui.progressBar.setRange(0, 1000)
        i = 0
        for dirname, dirnames, filenames in os.walk(g_dir):
            for filename in filenames:
                # Progress bar kludge
                i += 1
                if i >= 990:
                    i = 0
                self.ui.progressBar.setValue(i)
                self.ui.progressBar.update()
                fname = os.path.join(dirname, filename)
                # If the file name ends in "project.txt"
                if fname.find('project.txt') != -1:
                    station_name = filename.split('_')[0]
                    self.ui.statusbar.showMessage('Searching for .fg5 files in {}'.format(station_name))
                    self.ui.statusbar.update()
                    fg5 = FG5(fname)
                    if self.ui.startDateEdit.date() < fg5.dtime < self.ui.endDateEdit.date():
                        data.append(FG5(fname))
        self.ui.statusbar.showMessage('')
        return data

    def getdir_g(self):
        starting_dir = self.ui.gLineEdit.text()
        self.ui.gLineEdit.setText(self.get_dirname(starting_dir))

    def getdir_photo(self):
        starting_dir = self.ui.photoLineEdit.text()
        self.ui.photoLineEdit.setText(self.get_dirname(starting_dir))

    def getdir_cosmos(self):
        starting_dir = self.ui.cosmosLineEdit.text()
        self.ui.cosmosLineEdit.setText(self.get_dirname(starting_dir))

    def getdir_fieldsheet(self):
        starting_dir = self.ui.fieldsheetLineEdit.text()
        self.ui.fieldsheetLineEdit.setText(self.get_dirname(starting_dir))

    def getdir_GPS(self):
        starting_dir = self.ui.GPSLineEdit.text()
        self.ui.GPSLineEdit.setText(self.get_dirname(starting_dir))

    def get_dirname(self, starting_dir):
        dialog = QFileDialog()
        g_dir = dialog.getExistingDirectory(None, 'Open working directory', starting_dir)
        return g_dir


class ImgWidget(QWidget):
    # Widget to show photo preview
    def __init__(self, image_path, parent=None):
        super(ImgWidget, self).__init__(parent)
        pic = QPixmap(image_path)
        self.pic = pic.scaled(PICTURE_SIZE, PICTURE_SIZE, Qt.KeepAspectRatio)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pic.width(), self.pic.height(),
                           self.pic)

    def minimumSizeHint(self):
        return QSize(self.pic.width(), self.pic.height())

    def sizeHint(self):
        return QSize(self.pic.width(), self.pic.height())


class Calendar(QWidget):
    def __init__(self, parent=None):
        super(Calendar, self).__init__(parent)
        self.ui = Ui_Calendar()
        self.ui.setupUi(self)


class Preview(QDialog):
    def __init__(self, parent=None):
        super(Preview, self).__init__(parent)
        self.ui = Ui_PreviewWindow()
        self.ui.setupUi(self)
        self.setWindowFlags(self.windowFlags() |
                            Qt.WindowSystemMenuHint |
                            Qt.WindowMinMaxButtonsHint)

    def preview_file(self, item):
        if item.column() == 4:
            file = item.tableWidget().item(item.row(), 2).text()
            if 'GPS' in item.tableWidget().item(item.row(), 1).text():
                file = file.replace('T01', 'rnx')
            webbrowser.open(file)
        return

    def reject(self):
        self.ui.previewTableWidget.clearContents()
        self.ui.previewTableWidget.setRowCount(0)
        self.done(0)

    def process_data(self):
        """
        Does the copying.

        :return: None
        """
        self.ui.btn_OK.setEnabled(False)
        self.ui.btn_Cancel.setText('Close')
        for i in range(self.ui.previewTableWidget.rowCount()):
            if self.ui.previewTableWidget.item(i, 0).checkState():
                from_full_path = self.ui.previewTableWidget.item(i, 2).text()
                to_path = os.path.dirname(self.ui.previewTableWidget.item(i, 3).text())

                # Copy project files
                if from_full_path.find('.project.txt') > 0:
                    fn = os.path.basename(from_full_path)
                    fn_elems = fn.split('.')
                    fn = fn_elems[0]
                    for file in glob.glob(os.path.join(os.path.dirname(from_full_path), fn + '.*')):
                        if not os.path.exists(to_path):
                            os.makedirs(to_path)
                        try:
                            copy(file, to_path)
                        except:
                            self.ui.previewTableWidget.item(i, 1).setBackground(QColor(Qt.red))
                            self.ui.previewTableWidget.repaint()
                            text1 = 'Error copying g files: ' + os.path.basename(from_full_path)
                            MessageBox(text1, '')
                    gsf_files = glob_re(fn + r'[0-9][0-9][0-9].gsf',
                                        os.listdir(os.path.join(os.path.dirname(from_full_path))))
                    for file in gsf_files:
                        try:
                            copy(os.path.join(os.path.dirname(from_full_path), file), to_path)
                        except:
                            self.ui.previewTableWidget.item(i, 1).setBackground(QColor(Qt.red))
                            self.ui.previewTableWidget.repaint()
                            text1 = 'Error copying g files: ' + os.path.basename(from_full_path)
                            MessageBox(text1, '')
                    self.ui.previewTableWidget.item(i, 1).setBackground(QColor(Qt.green))
                    self.ui.previewTableWidget.repaint()

                # Copy cosmos data
                elif self.ui.previewTableWidget.item(i, 1).text().find('CR occupation') > 0:
                    cr_occ = self.ui.previewTableWidget.item(i, 1).cr_occ
                    try:
                        with open(self.ui.previewTableWidget.item(i, 3).text(), 'w') as fid:
                            fid.write(cosmos_header)
                            columns = list(cr_occ.df.columns)
                            fid.write(cr_occ.df.to_csv(sep=',',
                                                       index=False,
                                                       header=None,
                                                       columns=columns[:-2],
                                                       line_terminator='\n'))
                            self.ui.previewTableWidget.item(i, 1).setBackground(QColor(Qt.green))
                            self.ui.previewTableWidget.repaint()
                    except:
                        self.ui.previewTableWidget.item(i, 1).setBackground(QColor(Qt.red))
                        self.ui.previewTableWidget.repaint()

                # Copy photos
                elif self.ui.previewTableWidget.item(i, 1).text().find('Copy and rename photo') == 0:
                    from_path = self.ui.previewTableWidget.item(i, 2).text()
                    to_path = self.ui.previewTableWidget.item(i, 3).text()
                    if not os.path.exists(os.path.dirname(to_path)):
                        text1 = 'Site description directory not found: ' + os.path.basename(os.path.dirname(to_path))
                        MessageBox(text1, 'New directory created.')
                        os.makedirs(os.path.dirname(to_path))
                    try:
                        copyfile(from_path, to_path)
                    except:
                        text1 = 'Error copying photo: ' + os.path.basename(from_path)
                        MessageBox(text1, '')
                        self.ui.previewTableWidget.item(i, 1).setBackground(QColor(Qt.red))
                        self.ui.previewTableWidget.repaint()
                        continue
                    os.remove(from_path)
                    self.ui.previewTableWidget.item(i, 1).setBackground(QColor(Qt.green))
                    self.ui.previewTableWidget.repaint()

                # Copy fieldsheets
                elif self.ui.previewTableWidget.item(i, 1).text().find('Copy fieldsheet') == 0:
                    from_path = self.ui.previewTableWidget.item(i, 2).text()
                    to_path = self.ui.previewTableWidget.item(i, 3).text()
                    try:
                        copyfile(from_path, to_path)
                        os.remove(from_path)
                        self.ui.previewTableWidget.item(i, 1).setBackground(QColor(Qt.green))
                        self.ui.previewTableWidget.repaint()
                    except:
                        self.ui.previewTableWidget.item(i, 1).setBackground(QColor(Qt.red))
                        self.ui.previewTableWidget.repaint()
                        text1 = 'Error copying fieldsheet: ' + os.path.basename(from_path)
                        MessageBox(text1, '')

                # Copy GPS data
                elif self.ui.previewTableWidget.item(i, 1).text().find('GPS') > 0:
                    gps_occ = self.ui.previewTableWidget.item(i, 1).gps_occ
                    try:
                        rinex_path = self.ui.previewTableWidget.item(i, 3).text()
                        gps_path = os.path.dirname(rinex_path)
                        gps_original_basename = os.path.basename(gps_occ.file)
                        if not os.path.exists(gps_path):
                            os.makedirs(gps_path)
                        copyfile(gps_occ.file, rinex_path)
                        copyfile(gps_occ.file.replace('rnx', 't01'),
                                 os.path.join(gps_path, gps_original_basename.replace('rnx', 'T01')))
                        os.remove(gps_occ.file)
                        os.remove(gps_occ.file.replace('rnx', 'T01'))
                        os.remove(gps_occ.file.replace('rnx', 'dat'))
                        self.ui.previewTableWidget.item(i, 1).setBackground(QColor(Qt.green))
                        self.ui.previewTableWidget.repaint()
                    except:
                        self.ui.previewTableWidget.item(i, 1).setBackground(QColor(Qt.red))
                        self.ui.previewTableWidget.repaint()
        MessageBox('All done!', '')

    def export_summary(self):
        dialog = QFileDialog()
        filename, _ = dialog.getSaveFileName(None, 'Write preview table to file...')
        if filename[-4:-3] != '.':
            filename += '.txt'
        with open(filename, 'w') as fid:
            for i in range(self.ui.previewTableWidget.rowCount()):
                col_0 = str(self.ui.previewTableWidget.item(i, 0).checkState())
                if col_0 == '2':
                    col_0 = '1'
                col_1 = self.ui.previewTableWidget.item(i, 1).text()
                col_2 = self.ui.previewTableWidget.item(i, 2).text()
                col_3 = self.ui.previewTableWidget.item(i, 3).text()
                if filename[-3:] == 'csv':
                    fid.write('{},{},{},{}\n'.format(str(col_0), col_1, col_2, col_3))
                else:
                    fid.write('{}\t{}\t{}\t{}\n'.format(str(col_0), col_1, col_2, col_3))


class MessageBox(QMessageBox):
    def __init__(self, text1, text2=None, parent=None):
        super(MessageBox, self).__init__(parent)
        self.setIcon(QMessageBox.Information)
        self.setText(text1)
        self.setInformativeText(text2)
        self.addButton(QMessageBox.Ok)
        self.exec_()


def glob_re(pattern, strings):
    return filter(re.compile(pattern).match, strings)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
