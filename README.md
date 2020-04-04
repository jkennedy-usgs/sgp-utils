# sgp-utils
USGS Southwest Gravity Program absolute-gravity processing utilities

* fg5.py - given a project.txt file, returns a python object with relevant information
* fg5_parse.py - creates a tab-separated file with relevant information from a specified directory of project.txt files.
* fg5_plot.py - creates figures, one per station, showing gravity change over time, using a file created using A10_parse.py.
* fg5_SY_plot.py - plots gravity change (converted to feet of free-standing water) vs. groundwater-level change. The slope of this relation is an estimate of specific yield.
* fg5_WL_plot.py - plots gravity time series together with groundwater-level time series.
* fg5_toExcel.py - converts the text file output by fg5_parse.py into an Excel file (1 sheet per site) and retrieves groundwater-level data from NWIS.
* fg5_update.py - applies a laser drift correction and (or) soil moisture correction to the gravity value in a *.project.txt file.
* nwis.py - retrieves groundwater-level data for a USGS site from the National Water Information System (NWIS). 

* Ingestor - PyQt5 gui for archiving gravity, photo, COSMOS, GPS, fieldsheets after a field run.

The software and related documentation on these web pages were developed by the U.S. Geological Survey (USGS) for use by the USGS in fulfilling its mission. The software can be used, copied, modified, and distributed without any fee or cost. Use of appropriate credit is requested. The USGS provides no warranty, expressed or implied, as to the correctness of the furnished software or the suitability for any purpose. The software has been tested, but as with any complex software, there could be undetected errors.
