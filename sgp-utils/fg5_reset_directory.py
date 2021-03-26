#! python 3
"""
Script to cleanup the mess after running fg5_update to update project.txt files with laser-calibration correction.
If Final Data files are modified/reprocessed after running the update, it can get messy.
"""
import os
import shutil
import sys
from tkinter import filedialog

reset = 'HARD'


def launch_gui():
    # root = Tk()
    # root.withdraw()
    data_directory = filedialog.askdirectory()

    return data_directory


def reset_directory(directory):
    # Loop over directory
    no_original_but_prj_updated = []
    original_copied_to_prj = []
    kept_prj_deleted_original = []
    no_original_did_nothing = []

    for dirname, dirnames, filenames in os.walk(directory):


        for fn1 in filenames:
            if '.original.txt' in fn1:
                prj_file = str.replace(fn1, 'original.txt', 'project.txt')
                if os.path.exists(prj_file):
                    if os.path.getmtime(os.path.join(dirname, fn1)) < os.path.getmtime(os.path.join(dirname, prj_file)):
                        UPDATED = False
                        with open(prj_file, 'r') as fid:
                            for line in fid:
                                if 'Gravity value adjusted by' in line:
                                    UPDATED = True
                        if UPDATED:
                            shutil.move(os.path.join(dirname, fn1), os.path.join(dirname, prj_file))
                            original_copied_to_prj.append(prj_file)
                        else:
                            shutil.remove(os.path.join(dirname, str.replace(fn1)))
                            kept_prj_deleted_original.append(prj_file)
                    else:

                        jeff = 1
                # try:
                #     shutil.move(fn1, os.path.join(dirname, str.replace(fn1, 'original.txt', 'project.txt')))

        # If hard reset:
        # Delete .project.txt file
        # Copy .original.txt file to .project.txt file
        # Delete .original.txt file
    # If project.txt file is newer

        # and project.txt has "Laser updated by..."


if __name__ == "__main__":
    print(sys.argv)
    if len(sys.argv) == 1:
        directory = launch_gui()
    else:
        directory = sys.argv[1]
    reset_directory(directory)
