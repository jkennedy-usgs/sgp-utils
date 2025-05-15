"""
file/a10.py
===============

GSadjust object for absolute gravity observation
-------------------------------------------------------------------------------

Used to parse .project.txt files generated my Micro-g absolute-gravity meters

This software is preliminary, provisional, and is subject to revision. It is
being provided to meet the need for timely best science. The software has not
received final approval by the U.S. Geological Survey (USGS). No warranty,
expressed or implied, is made by the USGS or the U.S. Government as to the
functionality of the software and related material nor shall the fact of release
constitute any such warranty. The software is provided on the condition that
neither the USGS nor the U.S. Government shall be held liable for any damages
resulting from the authorized or unauthorized use of the software.
"""

import re
import datetime as dt

class A10:
    """
    GSadjust object for absolute gravity observation
    """

    def __init__(self, fn=None):
        self.created = None
        self.project = None
        self.stationname = None
        self.lat = None
        self.long = None
        self.elev = None
        self.setupht = None
        self.transferht = None
        self.actualht = None
        self.gradient = None
        self.nominalAP = None
        self.polarx = None
        self.polary = None
        self.dffile = None
        self.olfile = None
        self.clock = None
        self.blue = None
        self.red = None
        self.date = None
        self.time = None
        self.timeoffset = None
        self.gravity = None
        self.setscatter = None
        self.precision = None
        self.uncertainty = None
        self.collected = None
        self.processed = None
        self.transferhtcorr = None
        self.comments = None
        if fn:
            self.read_project_dot_txt(fn)

    def read_project_dot_txt(self, filename):
        """
        Read an A10 project.txt file, storing the result on this object.
        """
        dtf = False
        olf = False
        skip_grad = False
        in_comments = 0
        project_file = open(filename, "r", encoding="unicode_escape")
        data_array = []  # ['a']*32
        # Look for these words in the g file.
        tags = re.compile(
            r"Project|Name|Created|Setup|SN"
            r"|Transfer|Actual|Date|Time|TimeOffset|Nominal|Red"
            r"|Blue|Scatter|SetsColl|SetsProc|Precision|Total_unc"
        )
        # 'Lat' is special because there are three data on the same line:
        # (Lat, Long, Elev)
        lat_tag = re.compile(r"Lat")

        # 'Polar' is also special, for the same reason.
        pol_tag = re.compile(r"Polar")

        version_tag = re.compile(r"Version")
        version = 0

        # Apparently using a delta file is optional, it's not always written to the
        # .project file.
        delta_tag = re.compile(r"DFFile")
        ol_tag = re.compile(r"OLFile")
        rub_tag = re.compile(r"RubFrequency")
        grav_tag = re.compile(r"Grv")
        grad_tag = re.compile(r"Gradient")

        # This one, because "Gradient:" is repeated exactly in this section.
        unc_tag = re.compile(r"Uncertainties")

        # This deals with multi-line comments
        comment_tag = re.compile(r"Comments")
        comments = ""

        for line in project_file:
            # Change up some text in the g file to make it easier to parse
            # (remove duplicates, etc.)
            line = line.strip()
            line = line.replace("\n\n", "\n")
            line = line.replace(":  ", ": ")
            # Repeat to take care of ":   " (three spaces).
            line = line.replace(":  ", ": ")
            line = line.replace(":  ", ": ")
            line = line.replace("g Acquisition Version", "Acq")
            line = line.replace("g Processing ", "")
            line = line.replace("Project Name:", "Project")
            line = line.replace("File Created:", "Created")
            line = line.replace("Gravity Corrections", "grvcorr")
            line = line.replace(" Height:", ":")
            line = line.replace("Delta Factor Filename:", "DFFile")
            line = line.replace("Ocean Load ON, Filename:", "OLFile")
            line = line.replace("Nominal Air Pressure:", "Nominal")
            line = line.replace("Barometric Admittance Factor:", "Admittance")
            line = line.replace(" Motion Coord:", "")
            line = line.replace("Set Scatter:", "Scatter")
            line = line.replace("Offset:", "ofst")
            line = line.replace("Time Offset (D h:m:s):", "TimeOffset")
            line = line.replace("Ocean Load:", "OLC")
            line = line.replace("Rubidium Frequency:", "RubFrequency")
            line = line.replace("Blue Lock:", "Blue")
            line = line.replace("Red Lock:", "Red")
            line = line.replace("Red/Blue Separation:", "Separation")
            line = line.replace("Red/Blue Interval:", "Interval")
            line = line.replace("Gravity Corrections", "Corrections")
            line = line.replace("Gravity:", "Grv:")
            line = line.replace("Number of Sets Collected:", "SetsColl")
            line = line.replace("Number of Sets Processed:", "SetsProc")
            # This is the PM error, not the values.
            line = line.replace("Polar Motion:", "PolMotC")
            line = line.replace("Barometric Pressure:", "")
            line = line.replace("System Setup:", "")
            line = line.replace("Total Uncertainty:", "Total_unc")
            line = line.replace("Measurement Precision:", "Precision")
            line = line.replace("Meter S/N:", "SN")
            line = line.replace(":", "", 1)
            line = line.replace(",", "")
            line_elements = line.split(" ")

            # Look for tags.
            tags_found = re.search(tags, line)
            lat_tag_found = re.search(lat_tag, line)
            pol_tag_found = re.search(pol_tag, line)
            comment_tag_found = re.search(comment_tag, line)
            version_tag_found = re.search(version_tag, line)
            delta_tag_found = re.search(delta_tag, line)
            ol_tag_found = re.search(ol_tag, line)
            grav_tag_found = re.search(grav_tag, line)
            unc_tag_found = re.search(unc_tag, line)
            grad_tag_found = re.search(grad_tag, line)
            rub_tag_found = re.search(rub_tag, line)

            if unc_tag_found is not None:
                skip_grad = True

            if grad_tag_found is not None:
                if not skip_grad:
                    data_array.append(line_elements[1])

            # Old g versions don't output Time Offset, which comes right before gravity.
            if grav_tag_found is not None:
                if version < 5:
                    data_array.append("-999")
                data_array.append(line_elements[1])

            if delta_tag_found is not None:
                dtf = True
                df = " ".join(line_elements[1:])

            if ol_tag_found is not None:
                olf = True
                of = " ".join(line_elements[1:])

            if rub_tag_found is not None:
                if dtf:
                    data_array.append(df)
                else:
                    data_array.append("-999")
                if olf:
                    data_array.append(of)
                else:
                    data_array.append("-999")
                data_array.append(line_elements[1])

            if version_tag_found is not None:
                version = float(line_elements[1])

            if tags_found is not None:
                try:
                    data_array.append(line_elements[1])
                except:
                    data_array.append("-999")

            if lat_tag_found is not None:
                data_array.append(line_elements[1])
                data_array.append(line_elements[3])
                data_array.append(line_elements[5])
                # This accomodates old versions of g. If these data are to be published,
                # though, they should be reprocessed in a more recent version.
                if version < 5:
                    data_array.append("-999")  # Setup Height.
                    data_array.append("-999")  # Transfer Height.
                    data_array.append("-999")  # Actual Height.

            if pol_tag_found is not None:
                data_array.append(line_elements[1])
                data_array.append(line_elements[3])

            if in_comments > 0:
                comments += line
                if in_comments > 1:
                    comments += " | "
                in_comments += in_comments

            if comment_tag_found is not None:
                in_comments = 1

        data_array.append(comments)

        # Old g versions don't output transfer height correction.
        if version < 5:
            data_array.append("-999")
        project_file.close()

        self.created = data_array.pop(0)
        self.project = data_array.pop(0)
        self.stationname = data_array.pop(0)
        self.lat = data_array.pop(0)
        self.long = data_array.pop(0)
        self.elev = data_array.pop(0)
        self.setupht = data_array.pop(0)
        self.transferht = data_array.pop(0)
        self.actualht = data_array.pop(0)
        self.gradient = data_array.pop(0)
        self.nominalAP = data_array.pop(0)
        self.polarx = data_array.pop(0)
        self.polary = data_array.pop(0)
        self.sn = data_array.pop(0)
        self.dffile = data_array.pop(0)
        self.olfile = data_array.pop(0)
        self.clock = data_array.pop(0)
        self.blue = data_array.pop(0)[:-1]
        self.red = data_array.pop(0)[:-1]
        date_elems = data_array.pop(0).split("/")
        self.date = (
            str(int(date_elems[2]) + 2000) + "-" + date_elems[0] + "-" + date_elems[1]
        )
        self.time = data_array.pop(0)
        self.timeoffset = data_array
        self.gravity = data_array.pop(0)
        self.setscatter = data_array.pop(0)
        self.precision = data_array.pop(0)
        self.uncertainty = data_array.pop(0)
        self.collected = data_array.pop(0)
        self.processed = data_array.pop(0)
        self.transferhtcorr = data_array.pop(0)
        self.comments = data_array.pop(0)


def project_to_list(project_file):
    data_row = []
    dtf = False
    olf = False
    skip_grad = False

    # Look for these words in the g file
    tags = re.compile(r'Created|Setup|SN' +
                      r'|Transfer|Actual|Time|TimeOffset|Nominal|Red' +
                      r'|Blue|Scatter|SetsColl|SetsProc|Precision|BarPresCorr|Total_unc')

    # Dates need to be converted so excel can read them
    Date_tag = re.compile(r'Date')

    # 'Lat' is special because there are three data on the same line:
    # (Lat, Long, Elev)
    Lat_tag = re.compile(r'Lat')

    # 'Polar' is also special, for the same reason
    Pol_tag = re.compile(r'Polar')

    version = 0
    Version_tag = re.compile(r'Version')

    # Need this to accommodate station names with spaces
    Project_tag = re.compile(r'Project')
    Name_tag = re.compile(r'Name')

    # Apparently using a delta file is optional, it's not always written
    # to the .project file
    Delta_tag = re.compile(r'DFFile')
    OL_tag = re.compile(r'OLFile')
    Rub_tag = re.compile(r'RubFrequency')
    Grav_tag = re.compile(r'Grv')
    Grad_tag = re.compile(r'Gradient')

    # This one, because "Gradient:" is repeated exactly in this section
    Unc_tag = re.compile(r'Uncertainties')

    # This deals with multi-line comments
    inComments = False
    Comment_tag = re.compile(r'Comments')
    comments = ''

    for line in project_file:
        # Change up some text in the g file to make it easier to parse
        # (remove duplicates, etc.)
        line = str.strip(line)
        line = str.replace(line, '\n\n', '\n')

        Comment_tag_found = re.search(Comment_tag, line)
        if inComments:
            if comments == '':
                comments = line
            else:
                comments += ' | '
                comments += line
            continue
        elif Comment_tag_found is not None:
            inComments = True
            continue

        line = str.replace(line, ":  ", ": ")
        # Repeat to take care of ":   " (three spaces)
        line = str.replace(line, ":  ", ": ")
        line = str.replace(line, ":  ", ": ")
        line = str.replace(line, "g Acquisition Version", "Acq")
        line = str.replace(line, "g Processing ", "")
        line = str.replace(line, "Project Name:", "Project")
        line = str.replace(line, "File Created:", "Created")
        line = str.replace(line, 'Gravity Corrections', 'grvcorr')
        line = str.replace(line, " Height:", ":")
        line = str.replace(line, "Delta Factor Filename:", "DFFile")
        line = str.replace(line, "Ocean Load ON, Filename:", "OLFile")
        line = str.replace(line, "Nominal Air Pressure:", "Nominal")
        line = str.replace(line, "Barometric Admittance Factor:",
                           "Admittance")
        line = str.replace(line, " Motion Coord:", "")
        line = str.replace(line, "Set Scatter:", "Scatter")
        line = str.replace(line, "Offset:", "ofst")
        line = str.replace(line, "Time Offset (D h:m:s):", "TimeOffset")
        line = str.replace(line, "Ocean Load:", "OLC")
        line = str.replace(line, "Rubidium Frequency:", "RubFrequency")
        line = str.replace(line, "Blue Lock:", "Blue")
        line = str.replace(line, "Red Lock:", "Red")
        line = str.replace(line, "Red/Blue Separation:", "Separation")
        line = str.replace(line, "Red/Blue Interval:", "Interval")
        line = str.replace(line, "Gravity Corrections", "Corrections")
        line = str.replace(line, "Gravity:", "Grv:")
        line = str.replace(line, "Number of Sets Collected:", "SetsColl")
        line = str.replace(line, "Number of Sets Processed:", "SetsProc")
        # This is the PM error, not the values
        line = str.replace(line, "Polar Motion:", "PolMotC")
        line = str.replace(line, "Barometric Pressure:", "BarPresCorr")
        line = str.replace(line, "System Setup:", "")
        line = str.replace(line, "Total Uncertainty:", "Total_unc")
        line = str.replace(line, "Measurement Precision:", "Precision")
        line = str.replace(line, "Meter S/N:", "SN")
        line = str.replace(line, ":", "", 1)
        line = str.replace(line, ",", "")
        line_elements = str.split(line, " ")

        # Look for tags
        tags_found = re.search(tags, line)
        Lat_tag_found = re.search(Lat_tag, line)
        Pol_tag_found = re.search(Pol_tag, line)
        Version_tag_found = re.search(Version_tag, line)
        Delta_tag_found = re.search(Delta_tag, line)
        OL_tag_found = re.search(OL_tag, line)
        Grav_tag_found = re.search(Grav_tag, line)
        Unc_tag_found = re.search(Unc_tag, line)
        Grad_tag_found = re.search(Grad_tag, line)
        Rub_tag_found = re.search(Rub_tag, line)
        Name_tag_found = re.search(Name_tag, line)
        Project_tag_found = re.search(Project_tag, line)
        Date_tag_found = re.search(Date_tag, line)

        if Unc_tag_found is not None:
            skip_grad = True

        if Grad_tag_found is not None:
            if not skip_grad:
                data_row.append(line_elements[1])

        # Old g versions don't output Time Offset, which comes right
        # before gravity
        if Grav_tag_found is not None:
            if version < 5:
                data_row.append('-999')
            data_row.append(line_elements[1])

        if Delta_tag_found is not None:
            dtf = True
            df = " ".join(line_elements[1:])

        if OL_tag_found is not None:
            olf = True
            of = " ".join(line_elements[1:])

        if Rub_tag_found is not None:
            if dtf:
                data_row.append(df)
            else:
                data_row.append('-999')
            if olf:
                data_row.append(of)
            else:
                data_row.append('-999')
            data_row.append(line_elements[1])

        if Version_tag_found is not None:
            version = float(line_elements[1])

        if Name_tag_found is not None or Project_tag_found is not None:
            try:
                name = " ".join(line_elements[1:])
                data_row.append(name)
            except:
                data_row.append('-999')

        if tags_found is not None:
            try:
                data_row.append(line_elements[1])
            except:
                data_row.append('-999')

        if Date_tag_found is not None:
            data_row.append(line_elements[1])

        if Lat_tag_found is not None:
            data_row.append(line_elements[1])
            data_row.append(line_elements[3])
            data_row.append(line_elements[5])
            # This accommodates old versions of g. If these data are to
            # be published, though, they should be reprocessed in a more
            # recent version.
            if version < 5:
                data_row.append('-999')  # Setup Height
                data_row.append('-999')  # Transfer Height
                data_row.append('-999')  # Actual Height

        if Pol_tag_found is not None:
            data_row.append(line_elements[1])
            data_row.append(line_elements[3])
            # if version < 5:
            #     data_row.append('-999') # delta factor filename

        if inComments > 0:
            comments = comments + line
            if inComments > 1:
                comments = comments + ' | '
            inComments += inComments

        if Comment_tag_found is not None:
            inComments = 1
            comments = ''

    # Old g versions don't output transfer height correction
    if version < 5:
        data_row.append('-999')
    data_row.append(comments)
    return data_row
