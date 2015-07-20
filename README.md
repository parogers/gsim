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
    * Text wraps in source view?
    * Jump to selected line
    * Optimize rendering (particularly when seeking backwards)
    * Plugin - match coordinate systems - inkscape + laser
    * Save program preferences
    * Dimension render area?
    * Slider for speed control

Installation
------------

To run the G-Code simulator you will need:

    * Python 2.6 or later, including Python 3 (https://www.python.org/)
    * PyGObject (https://live.gnome.org/PyGObject)
    * Numpy (http://numpy.scipy.org)

Run the script from the command line:

    python gsim-launch.py

You can also view the parsed G-code with the command:

    python -m gsim.gcode

The program has been tested on Linux but should work in Windows as well.

License
-------

The source is released under the GPL v2 (or later). See LICENSE.txt for more details.


