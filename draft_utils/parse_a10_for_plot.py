# script to generate plots of A10 data, showing which sets are included in the final g value.

# open .drop.txt file for the project

# count the number of sets

# open .set.txt file

# count the number of sets there

# if the number of sets is the same, we can use the sigma values in the .set.txt file,
# plot the results. 

# otherwise, some sets have been excluded from the processing. The only data for these
# sets is the drop data, and no sigma is output. Therefore, we recalculate all of the 
# sigmas using the drop data. Because we don't have the exact formula used in the g
# software, we'll recalculate all of them for consistency.

# 1/26/2013: Spot-checked the 6/29/2012 measurement at SA-015A, using the STDEV.P 
# function in Excel. It was pretty good, the sigmas around 45 correlated well, although
# one high sigma (~115 in g file) was ~140 in Excel.

#extra = [station,date,time,g,corrections?]

# Now we have the data, plot it
#plot(good_data,removed_data,extra)
import pdb
import string
import re
import os
import numpy as np
from matplotlib import pyplot
from plot_a10 import plt_a10

data_directory = "D:\gfz-ftp\A10"
plot_num=0
# Each file is stored on one line of the data_array
output_line=0

#open file for overwrite (change to "r" to append)
# fout = open(filesavename,"w")

# For each file in the data_directory
stations = [d for d in os.listdir(data_directory) if os.path.isdir(os.path.join(data_directory, d))]
station_paths = [
        d for d in (os.path.join(data_directory, d1) for d1 in os.listdir(data_directory))
        if os.path.isdir(d)
    ]
print stations
print station_paths

for sta_idx, station in enumerate(stations):
    fig = pyplot.figure()
    num_plots=0
    print num_plots
    for dirname,dirnames,filenames in os.walk(station_paths[sta_idx]):  
        print dirname
        print dirnames
        print filenames
        if 'unpublished' in dirnames:
            dirnames.remove('unpublished')
        
    #    pdb.set_trace()
        for filename in filenames:
            fname = os.path.join(dirname, filename)

            # If the file name ends in "project.txt"
            sets_parsed = 0
            drops_parsed = 0
            if string.find(fname,'set.txt') != -1:
                g=[]
                sigma=[]
                sets=[]
                project_file = open(fname)

                # regexp to look for digits in first column
                tags = re.compile('\d')

                for line in project_file:
                    line = line.strip()
                    line_elements = line.split()
                    if re.search(tags,line_elements[0]):
                        sets.append(int(line_elements[0]))
                        g.append(float(line_elements[4]))
                        sigma.append(float(line_elements[5]))
                sets_parsed = 1
                project_file.close()
                drop_name = fname.replace("set","drop")
                all_sets = []
                project_file = open(drop_name)
                tags = re.compile('\d')
                g_drop=[]
                g_set=[]
                sigma_set=[]
                old_set_num = 1
                for line in project_file:
                    line = line.strip()
                    line_elements = line.split()
                    
                    if re.search(tags,line_elements[0]):
                        set_num=int(line_elements[0])    
                        if set_num == old_set_num:
                            g_drop.append(float(line_elements[5]))
                        else:
                            g_set.append(np.mean(g_drop))
                            sigma_set.append(np.std(g_drop))
                            all_sets.append(old_set_num)
                            g_drop=[]
                            g_drop.append(float(line_elements[5]))
                            old_set_num=set_num
                project_file.close()
                g_set.append(np.mean(g_drop))
                sigma_set.append(np.std(g_drop))
                all_sets.append(old_set_num)
       
                accepted_sets = [x for x in all_sets if x in sets]
                print accepted_sets
                rejected_sets = [x for x in all_sets if x not in sets]
                print rejected_sets

                g_mean = np.mean(g_set)
                g_min = g_set-g_mean
                num_plots+=1
                ax=fig.add_subplot(4,2,num_plots)
                ax.errorbar(all_sets,g_min,sigma_set,fmt='ro')
                ax.set_xlim([0,max(all_sets)+1])
                #~ if num_plots==1:
                    #~ pyplot.title(station)
                #~ pyplot.savefig(station+'.png')
                print fname
                print g_min
                plt_a10(g_min,sigma_set,all_sets,accepted_sets,rejected_sets,filename,pyplot)
            


