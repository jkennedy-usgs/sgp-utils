import os
import string

root_dir = '//igswztwwgszona/Gravity Data Archive/Absolute Data/A-10/Final Data/'
proj_dir = 'Imperial Valley/'
site_dir = 'transect 3'

out_file = 'g9files.txt'
gradient = '-3.12'
keystrokes = ['i']

with open(out_file, 'w') as fid:
    for dirname,dirnames,filenames in os.walk(root_dir + proj_dir + site_dir):
         if 'unpublished' in dirnames:
             dirnames.remove('unpublished')
         for filename in filenames:
             fname = os.path.join(dirname, filename)
             # If the file name ends in "project.txt"
             if string.find(fname,'.fg5') != -1:
                 fn = fname.split("\\")
                 fid.write(site_dir + ',' + fn[-2] + ',' + fn[-1] + '\n')
