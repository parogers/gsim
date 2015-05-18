# Python G-Code simulator
#
# Copyright (C) 2011 Peter Rogers
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

from __future__ import absolute_import, division, print_function

###########
# Imports #
###########

import math
import numpy
from gsim import gcode
import time
try:
    import gtk
    import gobject
except ImportError:
    print("ERROR - Cannot import gtk module. Please visit http://www.pygtk.org/")
    sys.exit()

###########
# Classes #
###########

class GCodeRenderWidget(gtk.DrawingArea):
#    _pathIndex = 0
#    _pathParam = 0
    # The gcode state
    _state = None
    _lastTime = None
    _startTime = None
    # Whether we are playing an animation
    _playing = False
    _eventID = None
    _paths = None
    _pixmap = None
    # Whether a repaint is needed
    _repaint = True
    _zoomLevel = 1
    _border = 10
    # The number of pixels per mm
    _resolution = 1
    # Position of the cutting head
    _headPos = None
    _offset = None

    def __init__(this):
        gtk.DrawingArea.__init__(this)
        this.connect("expose-event", this.expose_cb)
        this._startTime = time.time()
        this._lastTime = 0
        this._currentTime = 0
        this._resolution = gtk.gdk.screen_height() / float(gtk.gdk.screen_height_mm())
        this._offset = (0, 0)

    def get_view_pos(this):
        return this._offset

    def set_view_pos(this, pos):
        this._offset = pos
        this.queue_draw()

    # Returns the size of the rendered geometry, taking into account the screen resolution
    # but ignoring the zoom factor.
    def get_render_size(this):
        if (not this._state):
            return None
        w = (this._state.maxPos[0]-this._state.minPos[0]+2*this._border)*this._resolution
        h = (this._state.maxPos[1]-this._state.minPos[1]+2*this._border)*this._resolution
        return (w, h)

    # Start / stop playing the job animation
    def set_playing(this, b):
        if (this._playing != b and this._state):
            this._playing = b
            if (b):
                # Start playing the job animation
                this._startTime = time.time()
                this._lastTime = this._startTime
                this._eventID = gobject.timeout_add(100, this.animate_cb)
            else:
                # Stop playing the animation
                if (this._eventID):
                    gobject.source_remove(this._eventID)
                    this._eventID = None

    def set_time(this, tm):
        this._currentTime = tm
        this._startTime = time.time()
        this._lastTime = this._startTime
        this._repaint = True
        this.queue_draw()
        this.emit("time-changed", this._currentTime)

    def get_time(this):
        return this._currentTime

    def get_playing(this):
        return this._playing

    def get_head_pos(this):
        return this._headPos

    # Set the machine state to display on this canvas
    def set_machine_state(this, state):
        this._state = state
        this._paths = state.paths
        this._playing = False
        this._headPos = None
        this.set_time(0)
        this.update_size()
        this.queue_draw()

    def set_zoom(this, zoom):
        this._zoomLevel = zoom
        this._repaint = True
        this.update_size()
        this.queue_draw()

    def get_zoom(this):
        return this._zoomLevel

    def update_size(this):
        w = this._zoomLevel * (this._state.maxPos[0]-this._state.minPos[0])+2*this._border
        h = this._zoomLevel * (this._state.maxPos[1]-this._state.minPos[1])+2*this._border
        #this.set_size_request(int(w*this._resolution), int(h*this._resolution))

    # Returns the path object currently being rendered
    def get_current_path(this):
        if (not this._paths):
            return None
        for path in this._paths:
            if (this._currentTime < path.startTime+path.duration):
                return path
        return this._paths[-1]

    def repaint_buffer(this):
        (canvasWidth, canvasHeight) = this.window.get_size()

#        if (not this._pixmap or this._pixmap.get_size() != (w,h)):
#            this._repaint = True
#            this._pixmap = gtk.gdk.Pixmap(this.window, w, h)

#        if (not this._repaint):
#            # A repaint is not needed
#            return
#        this._repaint = False

        # Calculate which path object is being rendered at this time
        currentPath = this.get_current_path()
        if (not currentPath):
            return

        if (currentPath.duration == 0):
            pathParam = 1
        else:
            pathParam = (this._currentTime-currentPath.startTime)/currentPath.duration

        # Create a cairo context which we will use to do the rendering
        cr = this.window.cairo_create()
#        cr = this._pixmap.cairo_create()
        #cr.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        #cr.clip()

        cr.set_source_rgb(1,1,1)
        cr.rectangle(0, 0, canvasWidth, canvasHeight)
        cr.fill()

        cr.set_source_rgb(0,0,0)
        cr.rectangle(0, 0, canvasWidth, canvasHeight)
        cr.stroke()

        cr.select_font_face("Times")
        cr.set_font_size(12)

        # Draw the geometry scale in the lower-left corner
        if (this._state.units == "mm"):
            units = "cm"
            mag = 10
        else:
            units = this._state.units
            mag = 1

        # Draw the scale in the bottom-right corner
        w = this._resolution*mag*this._zoomLevel
        h = w/3
        h = max(h, 5)
        h = min(h, 15)

        x1 = canvasWidth-w-10
        yp = canvasHeight-10
        x2 = x1+w

        # Draw a horizontal line
        cr.set_source_rgb(0,0,1)
        cr.move_to(x1, yp)
        cr.line_to(x2, yp)
        cr.stroke()
        # Draw the tick on the left side
        cr.move_to(x1, yp-h/2)
        cr.line_to(x1, yp+h/2)
        cr.stroke()
        # Draw the tick on the right side
        cr.move_to(x2, yp-h/2)
        cr.line_to(x2, yp+h/2)
        cr.stroke()
        # Show the units
        cr.move_to(x1-30, yp)
        cr.show_text("1 %s" % units)
        cr.stroke()

        cr.set_source_rgb(0,0,0)

        # Make the line thickness constant across all zoom levels
        cr.set_line_width(0.4/this._zoomLevel)

        cr.translate(this._offset[0], this._offset[1])

        # Change the coordinate system we are using to make things easier below. Since the
        # screen has (0, 0) in the upper-left corner, we need to translate everything 
        # down to start at the bottom of the screen, then reflect it back up (mathematical
        # y-axis goes up, but rendering y-axis goes down).
        cr.translate(0, canvasHeight)
        cr.scale(1, -1)

        # Convert mm to pixel coordinates
        cr.scale(this._resolution, this._resolution)
        # Now apply the user-defined zoom factor
        cr.scale(this._zoomLevel, this._zoomLevel)
        # Shift everything so that geometry is always visible
        cr.translate(-this._state.minPos[0]+this._border, 
                     -this._state.minPos[1]+this._border)

        lineCount = 0
        t = time.time()
        lastPos = None
        for path in this._paths:
            if (isinstance(path, gcode.Line)):
                # Plotting a linear path
                if (path == currentPath):
                    end = path.start + (path.end-path.start)*pathParam
                else:
                    end = path.end

                if (path.rapid):
                    # Rapid movement (spindle should be off here)
                    cr.set_source_rgb(1,0.5,1)
                else:
                    # Cutting movement
                    cr.set_source_rgb(0,0,0)
                # Draw the line
                cr.move_to(*path.start)
                cr.line_to(*end)
                cr.stroke()
                lineCount += 1
                lastPos = end.copy()

            elif (isinstance(path, gcode.Arc)):
                # Plotting an arc path
                angle1 = path.angle1
                angle2 = path.angle2

                if (path == currentPath):
                    if (abs(angle2-angle1) > math.pi):
                        if (angle1 < math.pi):
                            angle2 -= 2*math.pi
                        else:
                            angle2 += 2*math.pi

                    angle2 = angle1 + (angle2-angle1)*pathParam

                # Calculate the end position of the arc, so we can position the cutting head below
                lastPos = path.center + numpy.array([path.radius*math.cos(angle2), path.radius*math.sin(angle2)])

                # Normally the arc is rendered in the counter-clockwise direction
                if (path.clockwise):
                    (angle1, angle2) = (angle2, angle1)

                # Finally render the arc
                if (abs(angle1-angle2) > 0.06): #path.length > 0.5):
                    cr.set_source_rgb(0,0,0)
                    cr.arc(
                        path.center[0], 
                        path.center[1], path.radius, angle1, angle2)
                    cr.stroke()
                else:
                    # Draw the line
                    cr.set_source_rgb(0,0,0)
                    cr.move_to(*path.start)
                    cr.line_to(*lastPos)
                    cr.stroke()

            if (path == currentPath):
                break

        if (lastPos is not None):
            # Render the cutting head
            (xp, yp) = lastPos
            size = 1.5
            cr.set_source_rgb(1,0,0)
            cr.arc(xp, yp, size, 0, 2*math.pi)
            cr.stroke()
            this._headPos = lastPos.copy()

    # Called when this widget needs to be rendered
    def expose_cb(this, dwg, event):
        if (this._playing):
            # Advance the clock
            this._currentTime += time.time()-this._lastTime
            # Keep within the timeline
            this._currentTime = max(0, this._currentTime)
            if (this._currentTime > this._state.get_run_length()):
                # Stop playing
                this._currentTime = this._state.get_run_length()
                this._playing = False
            this._lastTime = time.time()
            this.emit("time-changed", this._currentTime)
            this._repaint = True

        this.repaint_buffer()
#        if (this._pixmap):
#            gc = this.get_style().white_gc
#            this.window.draw_drawable(gc, this._pixmap, 0, 0, 0, 0, -1, -1)

    def animate_cb(this, *args):
        this.queue_draw()
        return True

gobject.signal_new("time-changed", GCodeRenderWidget, 
    gobject.SIGNAL_RUN_LAST,
    gobject.TYPE_NONE,
    (gobject.TYPE_FLOAT,))

