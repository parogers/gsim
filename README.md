Python G-Code Simulator
=======================
Author: Peter Rogers (peter.rogers@gmail.com)

Simulates execution of a G-Code script. Supported codes:

    * Comments
    * Assignments
    * G00 - Rapid positioning
    * G01 - Linear interpolation
    * G02 - Circle interpolation (CW)
    * G03 - Circle interpolation (CCW)
    * G04 - Dwell
    * G21 - Units in mm (buggy)
    * M02 - End program
    * M03 - Spindle on
    * M05 - Spindle off
    * M06 - Tool change
    * Txx - Tool selection

Features:

    * Simulates the execution of a gcode script (.ngc file)
    * Renders the job in the XY plane (other views not supported)
    * Displays commands as they are executed
    * A slider lets you scrub through the job's timeline

Future plans:

    * Add support for more gcode commands
    * Render the job with configurable colors
    * Include a listing of the script in a side panel
    * Script editor?

Installation
------------

To run the G-Code simulator you will need:

    * Python 2.6 or later (probably runs on Python 3)
    * GTK for Python (http://www.pygtk.org)
    * Numpy (http://numpy.scipy.org)

Run the script from the command-line:

    python main.py

The program has been tested on Linux but should work in Windows as well.

License
-------

The source is released under the GPL v2 license. See LICENSE.txt for more details.


