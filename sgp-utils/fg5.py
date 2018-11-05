import string
import re


class FG5(object, fn=None):
    def __init__(self):
        self.created = None
        self.project = None
        self.stationname = None
        self.lat = float
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
        dtf = False
        olf = False
        skip_grad = False
        # in_comments = 0
        project_file = open(filename)
        data_array = []  # ['a']*32
        # Look for these words in the g file
        tags = re.compile(r'Created|Setup' +
                          r'|Transfer|Actual|Date|Time|TimeOffset|Nominal|Red' +
                          r'|Blue|Scatter|SetsColl|SetsProc|Precision|Total_unc')
        # 'Lat' is special because there are three data on the same line:
        # (Lat, Long, Elev)
        lat_tag = re.compile(r'Lat')

        # 'Polar' is also special, for the same reason
        pol_tag = re.compile(r'Polar')

        version_tag = re.compile(r'Version')

        # Apparently using a delta file is optional, it's not always written to the .project file
        delta_tag = re.compile(r'DFFile')
        ol_tag = re.compile(r'OLFile')
        rub_tag = re.compile(r'RubFrequency')
        grav_tag = re.compile(r'Grv')
        grad_tag = re.compile(r'Gradient')

        # This one, because "Gradient:" is repeated exactly in this section
        unc_tag = re.compile(r'Uncertainties')

        # This deals with multi-line comments
        comment_tag = re.compile(r'Comments')

        for line in project_file:
            # Change up some text in the g file to make it easier to parse
            # (remove duplicates, etc.)
            line = string.strip(line)
            line = string.replace(line, '\n\n', '\n')
            line = string.replace(line, ":  ", ": ")
            # Repeat to take care of ":   " (three spaces)
            line = string.replace(line, ":  ", ": ")
            line = string.replace(line, ":  ", ": ")
            line = string.replace(line, "g Acquisition Version", "Acq")
            line = string.replace(line, "g Processing ", "")
            line = string.replace(line, "Project Name:", "Project")
            line = string.replace(line, "File Created:", "Created")
            line = string.replace(line, 'Gravity Corrections', 'grvcorr')
            line = string.replace(line, " Height:", ":")
            line = string.replace(line, "Delta Factor Filename:", "DFFile")
            line = string.replace(line, "Ocean Load ON, Filename:", "OLFile")
            line = string.replace(line, "Nominal Air Pressure:", "Nominal")
            line = string.replace(line, "Barometric Admittance Factor:", "Admittance")
            line = string.replace(line, " Motion Coord:", "")
            line = string.replace(line, "Set Scatter:", "Scatter")
            line = string.replace(line, "Offset:", "ofst")
            line = string.replace(line, "Time Offset (D h:m:s):", "TimeOffset")
            line = string.replace(line, "Ocean Load:", "OLC")
            line = string.replace(line, "Rubidium Frequency:", "RubFrequency")
            line = string.replace(line, "Blue Lock:", "Blue")
            line = string.replace(line, "Red Lock:", "Red")
            line = string.replace(line, "Red/Blue Separation:", "Separation")
            line = string.replace(line, "Red/Blue Interval:", "Interval")
            line = string.replace(line, "Gravity Corrections", "Corrections")
            line = string.replace(line, "Gravity:", "Grv:")
            line = string.replace(line, "Number of Sets Collected:", "SetsColl")
            line = string.replace(line, "Number of Sets Processed:", "SetsProc")
            line = string.replace(line, "Polar Motion:", "PolMotC")  # This is the PM error, not the values
            line = string.replace(line, "Barometric Pressure:", "")
            line = string.replace(line, "System Setup:", "")
            line = string.replace(line, "Total Uncertainty:", "Total_unc")
            line = string.replace(line, "Measurement Precision:", "Precision")
            line = string.replace(line, ":", "", 1)
            line = string.replace(line, ",", "")
            line_elements = string.split(line, " ")

            # Look for tags
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

            # Old g versions don't output Time Offset, which comes right before gravity
            if grav_tag_found is not None:
                if version < 5:
                    data_array.append('-999')
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
                    data_array.append('-999')
                if olf:
                    data_array.append(of)
                else:
                    data_array.append('-999')
                data_array.append(line_elements[1])

            if version_tag_found is not None:
                version = float(line_elements[1])

            if tags_found is not None:
                try:
                    data_array.append(line_elements[1])
                except:
                    data_array.append('-999')

            if lat_tag_found is not None:
                data_array.append(line_elements[1])
                data_array.append(line_elements[3])
                data_array.append(line_elements[5])
                # This accomodates old versions of g. If these data are to be published,
                # though, they should be reprocessed in a more recent version.
                if version < 5:
                    data_array.append('-999')  # Setup Height
                    data_array.append('-999')  # Transfer Height
                    data_array.append('-999')  # Actual Height

            if pol_tag_found is not None:
                data_array.append(line_elements[1])
                data_array.append(line_elements[3])

            if in_comments > 0:
                comments += line
                if in_comments > 1:
                    comments += ' | '
                in_comments += in_comments

            if comment_tag_found is not None:
                in_comments = 1
                comments = ''

        data_array.append(comments)

        # Old g versions don't output transfer height correction
        if version < 5:
            data_array.append('-999')
        project_file.close()

        self.created = data_array[0]
        self.project = data_array[1]
        self.stationname = data_array[2]
        self.lat = data_array[3]
        self.long = data_array[4]
        self.elev = data_array[5]
        self.setupht = data_array[6]
        self.transferht = data_array[7]
        self.actualht = data_array[8]
        self.gradient = data_array[9]
        self.nominalAP = data_array[10]
        self.polarx = data_array[11]
        self.polary = data_array[12]
        self.dffile = data_array[13]
        self.olfile = data_array[14]
        self.clock = data_array[15]
        self.blue = data_array[16]
        self.red = data_array[17]
        self.date = data_array[18]
        self.time = data_array[19]
        self.timeoffset = data_array[20]
        self.gravity = data_array[21]
        self.setscatter = data_array[22]
        self.precision = data_array[23]
        self.uncertainty = data_array[24]
        self.collected = data_array[25]
        self.processed = data_array[26]
        self.transferhtcorr = data_array[27]
        self.comments = data_array[28]
