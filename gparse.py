#!/usr/bin/env python

import re
import os
import sys

from gsim import gcode

try:
    path = sys.argv[1]
except:
    print "usage: gparse.py gcodepath"
    sys.exit()

prog = gcode.parse_program(path)
state = prog.start()

while not state.finished:
    state.step()

print(state.paths)

#print state.variables

#for st in prog.statements:
#    print st.code, st.comment


