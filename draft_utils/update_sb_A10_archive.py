# Script to sync Gravity Data Archive at Arizona Water Science Center with online ScienceBase repository
import SbSession
import time
from A10 import A10project
import os
import string
import sys
from time import strftime
import shutil

sb = SbSession.SbSession()

# master key to gravity data archive (i.e., https://www.sciencebase.gov/catalog/item/56e301cae4b0f59b85d3a346)
gda_key = '56e301cae4b0f59b85d3a346'
gda_path = '\\\\Igswztwwwsgrav\\Shared\\Gravity Data Archive\\Absolute Data\\A-10\\Final Data'  # Path on local computer
gda_path = 'E:\\Shared\\current\\python\\AZWSC_Gravity\\TestFiles'

# Text file of directories to sync, 1 file per line
sync_dir_file = 'directories_to_sync.txt'

# Directory to temporarily download ScienceBase items. Items are deleted once they are synced.
temp_dir = 'E:\\Shared\\current\\python\\AZWSC_Gravity\\tempsb'
if not os.path.isdir(temp_dir):
    os.mkdir(temp_dir)

sb_grav_dic = {}
sb_studyarea_dic = {}
sb_station_dic = {}

# lists to hold output messages
out_synced_files = {}
out_synced_keys = []
out_files_on_sb_not_local = []
out_files_uploaded = []
out_files_sb_duplicate = []
out_messages = []
out_sb_studyareas_created = []
out_sb_stations_created = []
out_files_overwritten = []
out_files_not_uploaded = []

log_file = 'GravityDataArchive_SBsync_' + strftime("%Y%m%d-%H%M") + '.txt'

# Coordinates will be taken from the first g file for a station
add_coordinates = True

out_messages.append('Gravity Data Archive file sync')
out_messages.append('Start: ' + strftime("%Y-%m-%d %H:%M:%S"))

print 'Logging in...'
# username = raw_input("Username:  ")
# sb.loginc(str(username))
sb.login('xxxxxx','xxxxxx')
time.sleep(3)  # as per pysb documentation

# Throughout, 'keys' are the 24-digit ScienceBase id
studyarea_keys = sb.get_child_ids(gda_key)

# Retrieve all files from ScienceBase
print 'Downloading files from ScienceBase'
sys.stdout.flush()
for studyarea_key in studyarea_keys:
    sb_studyarea = sb.get_item(studyarea_key)

    # dic of study area names, e.g., 'TAMA', 'San Pedro', 'Imperial Valley'
    sb_studyarea_dic[studyarea_key] = sb_studyarea['title']
    station_keys = sb.get_child_ids(studyarea_key)

    for st_key in station_keys:
        station = sb.get_item(st_key)
        sb_station_dic[(studyarea_key, st_key)] = sb_studyarea['title'] + '\\' + station['title']
        # download files
        local_tmp_dir = os.path.join(temp_dir, sb_studyarea['title'], station['title'])
        if not os.path.exists(local_tmp_dir):
            os.makedirs(local_tmp_dir)
        sb.get_item_files(station, local_tmp_dir)

# Get g, etc. for files in ScienceBase
print 'Reading files'
sys.stdout.flush()
for dirname, dirnames, filenames in os.walk(temp_dir):
    for filename in filenames:
        a = A10project()
        a.read_project_dot_txt(os.path.join(dirname, filename))

        # Identify unique stations based on name, date, and g
        unique_key = (a.stationname, a.date, a.gravity)
        if unique_key not in sb_grav_dic:
            filepath = dirname.split('\\')[-2] + '\\' + dirname.split('\\')[-1] + '\\' + filename
            sb_grav_dic[unique_key] = filepath.upper()
        else:
            out_files_sb_duplicate.append(dirname.split('\\')[-2] + '\\' + dirname.split('\\')[-1] + '\\' + filename + ", " + sb_grav_dic[unique_key])

# Iterate over local directories specified in directories_to_sync.txt
print 'Reading local files'
sys.stdout.flush()
with open(os.path.join(gda_path, sync_dir_file)) as fid:
    for local_study_area in fid:
        local_study_area = local_study_area.strip()
        # Check if there is a SB item for the study area
        if local_study_area not in sb_studyarea_dic.values():
            print 'Creating new SB study area: ' + local_study_area
            # if not, create SB item under GDA root level
            new_item = {'title': local_study_area,
                        'parentId': gda_key}
            new_item = sb.create_item(new_item)
            sb_studyarea_dic[new_item['id']] = local_study_area
            out_sb_studyareas_created.append(local_study_area)

        # find SB key that corresponds to study area
        for studyarea_key in sb_studyarea_dic:
            if sb_studyarea_dic[studyarea_key] == local_study_area:
                break

        # Iterate over local gda, check if they match files downloaded
        for dirname, dirnames, filenames in os.walk(os.path.join(gda_path, local_study_area)):
            if 'unpublished' in dirnames:
                dirnames.remove('unpublished')
            for filename in filenames:
                fname = os.path.join(dirname, filename)
                if string.find(fname, 'project.txt') != -1:
                    local_archive_dir = dirname.split('\\')[-3] + '\\' + dirname.split('\\')[-2] + '\\' + filename
                    local_archive_dir= local_archive_dir.upper()
                    a = A10project()
                    a.read_project_dot_txt(os.path.join(dirname, filename))
                    unique_key = (a.stationname, a.date, a.gravity)
                    if local_archive_dir in sb_grav_dic.values():  # local file has same study area\station\filename as SB
                        if unique_key not in sb_grav_dic:  # file exists, but name or date or g are different
                            # get key that corresponds to stationname
                            for st_key in sb_station_dic:
                                if sb_station_dic[st_key] == a.stationname:
                                    station_exists = True
                                    break  # st_key corresponds to stationname
                            # TODO: delete old file; if necessary, create new station
                            sb.upload_files_and_update_item(sb.get_item(st_key[1]), [fname])
                            out_files_overwritten.append(local_archive_dir)
                        else:  # file exists in Sciencebase with same file name, station name, date, g
                            out_synced_files[unique_key] = sb_grav_dic[unique_key]
                            os.remove(os.path.join(temp_dir, sb_grav_dic[unique_key]))
                    elif unique_key in sb_grav_dic:  # there's already a file with the same name/date/g
                        out_files_not_uploaded.append('LOCAL FILE '
                                            + dirname.split('\\')[-2] + '\\' + dirname.split('\\')[-1] + '\\'
                                            + filename + '\n'
                                            + ' | SB FILE ' + sb_grav_dic[unique_key])
                    else:  # local study area\station\filename not found in ScienceBase, upload
                        station_exists = False
                        for st_key in sb_station_dic:
                            if sb_station_dic[st_key] == a.stationname:
                                station_exists = True
                                break
                            # if it doesn't, create it
                        if not station_exists:
                            new_station = {'title': a.stationname,
                                           'parentId': studyarea_key}
                            if add_coordinates:
                                new_station['spatial'] = {'representationalPoint':[float(a.long), float(a.lat)]}
                            print 'Creating station: ' + a.stationname
                            new_station = sb.create_item(new_station)
                            st_key = (studyarea_key, new_station['id'])
                            sb_station_dic[st_key] = a.stationname
                            out_sb_stations_created.append(dirname.split('\\')[-3]
                                                           + '\\' + dirname.split('\\')[-2]
                                                           + '\\' +a.stationname)

                        # upload file to appropriate study area and station
                        sb.upload_files_and_update_item(sb.get_item(st_key[1]), [fname])
                        out_files_uploaded.append(fname)

# check if there's any files left in tempsb (files in ScienceBase not in local directory)
for dirname, dirnames, filenames in os.walk(temp_dir):
    for filename in filenames:
        out_files_on_sb_not_local.append(dirname.split('\\')[-2] + '\\' + dirname.split('\\')[-1] + '\\' + filename)
        os.remove(os.path.join(dirname, filename))

out_messages.append('Finished: ' + strftime("%Y-%m-%d %H:%M:%S"))

os.rename(temp_dir,'junk')
shutil.rmtree('junk')
time.sleep(3)
os.makedirs(temp_dir)

with open(log_file, 'w') as fid_out:
    for line in out_messages:
        fid_out.write(line + '\n')
    fid_out.write('\n')
    fid_out.write('=====================================================================\n')

    fid_out.write('Duplicate files on ScienceBase, based on station name, date, and g:\n')
    for line in out_files_sb_duplicate:
        fid_out.write(line + '\n')
    fid_out.write('\n')
    fid_out.write('=====================================================================\n')

    fid_out.write('Files skipped because there''s already a file with the same station name, date, and g\n')
    fid_out.write('(May be flagged because the station name in the g file\n')
    fid_out.write('differs from the station directory name)\n')
    for line in out_files_sb_duplicate:
        fid_out.write(line + '\n')
    fid_out.write('\n')
    fid_out.write('=====================================================================\n')

    fid_out.write('Study areas created in ScienceBase:\n')
    for line in out_sb_studyareas_created:
        fid_out.write(line + '\n')
    fid_out.write('\n')
    fid_out.write('=====================================================================\n')

    fid_out.write('Stations created in ScienceBase:\n')
    for line in out_sb_stations_created:
        fid_out.write(line + '\n')
    fid_out.write('\n')
    fid_out.write('=====================================================================\n')

    fid_out.write('Files overwritten (same filename, different station name or date or g):\n')
    for line in out_files_overwritten:
        fid_out.write(line + '\n')
    fid_out.write('\n')
    fid_out.write('=====================================================================\n')

    fid_out.write('Files uploaded to ScienceBase:\n')
    for line in out_files_uploaded:
        fid_out.write(line + '\n')
    fid_out.write('\n')
    fid_out.write('=====================================================================\n')

    fid_out.write('Files already in ScienceBase:\n')
    file_list = out_synced_files.values()
    file_list.sort()
    for v in file_list:
        fid_out.write(v + '\n')
    fid_out.write('\n')
    fid_out.write('=====================================================================\n')

    fid_out.write('Files in ScienceBase, but not in local archive:\n')
    fid_out.write('(May be flagged because the station name in the g file\n')
    fid_out.write('differs from the station directory name)\n')
    for line in out_files_on_sb_not_local:
        fid_out.write(line + '\n')
    fid_out.write('\n')
    fid_out.write('=====================================================================\n')
