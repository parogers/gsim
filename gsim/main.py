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

from gi.repository import Pango
import sys
try:
    from gi.repository import Gtk
    from gi.repository import Gdk
    from gi.repository import GObject
except ImportError:
    print("ERROR - Cannot import gtk module. Please visit http://www.pyGtk.org/")
    sys.exit()

from gsim import gcode
from gsim.render import GCodeRenderWidget

#############
# Constants #
#############

VERSION = "0.21"

#############
# Functions #
#############

# Display a message box to the user, wait for it to close
def show_message(win, msg):
    w = Gtk.MessageDialog(win, buttons=Gtk.ButtonsType.OK)
    w.set_markup(msg)
    w.run()
    w.destroy()

###########
# Classes #
###########

class MainWindow(object):
    sliderChangedID = -1
    timeSlider = None
    timeAdjust = None
    dragging = False
    dragStart = None
    dragMouseStart = None
    # The various menu buttons
    openButton = None
    playButton = None
    rewindButton = None
    stopButton = None
    zoomInButton = None
    zoomOutButton = None
    zoomFitButton = None
    # The gcode machine state
    state = None

    def __init__(this):
        this.window = Gtk.Window()
        this.window.set_title("GCode Simulator")
        this.window.set_size_request(800, 500)
        this.window.connect("delete-event", Gtk.main_quit)

        # Create a vertical box to hold everything
        vbox = Gtk.VBox()
        vbox.show()
        this.window.add(vbox)

        # Build the main menu
        menu = this.build_menu()
        vbox.pack_start(menu, False, False, padding=0)

        # Create a timeline slider
        adj = Gtk.Adjustment(value=0, lower=0, upper=100, step_incr=0.1, page_incr=1, page_size=1)
        this.sliderChangedID = adj.connect("value-changed", this.time_slider_changed_cb)
        slider = Gtk.HScale(adjustment=adj)
        slider.show()
        this.timeSlider = slider
        this.timeAdjust = adj

        vbox.pack_start(slider, False, False, padding=4)

        hbox = Gtk.HPaned()
        hbox.show()
        vbox.pack_start(hbox, True, True, padding=0)

        # Create the drawing canvas
        this.renderArea = GCodeRenderWidget()
        this.renderArea.add_events(Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK)
        this.renderArea.connect("time-changed", this.time_changed_cb)
        this.renderArea.connect("motion-notify-event", this.mouse_motion_cb)
        this.renderArea.connect("button-press-event", this.mouse_button_cb)
        this.renderArea.connect("button-release-event", this.mouse_button_cb)
        this.renderArea.show()
        #vbox.pack_start(this.renderArea, True, True)
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        frame.show()
        frame.add(this.renderArea)
        hbox.pack1(frame, resize=True)

        # Add the program source area
        text = Gtk.TextView()
        text.show()
        text.set_editable(False)
        text.set_property("can-focus", False)
        this.programText = text
        scroll = Gtk.ScrolledWindow()
        scroll.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        scroll.show()
        scroll.add(text)
        hbox.pack2(scroll, resize=False)

        buf = text.get_buffer()
        numbersTag = buf.create_tag("numbers")
        numbersTag.set_property("background", "#f0f0f0")
        numbersTag.set_property("weight", Pango.Weight.LIGHT)

        # Create a tag for highlighted lines
        tag = buf.create_tag("highlight")
        tag.set_property("background", "#f03030")

        (w, h) = this.window.get_size()
        scroll.set_size_request(w//3, -1)

        # Create a box at the bottom of the window to hold the status label and coordinates label
        hbox = Gtk.HBox()
        hbox.show()
        vbox.pack_start(hbox, False, False, padding=0)

        # Create a status bar
        this.statusLabel = Gtk.Label()
        this.statusLabel.set_alignment(-1, 0)
        this.statusLabel.set_padding(4, 4)
        this.statusLabel.show()
        hbox.pack_start(this.statusLabel, True, True, padding=0)

        # Now create the label
        this.coordsLabel = Gtk.Label()
        this.coordsLabel.show()
        hbox.pack_start(this.coordsLabel, False, False, padding=0)

        # Update the window status
        this.update_status()
        this.window.show()

    def load_program(this, path):
        # Run the gcode program
        prog = gcode.parse_program(path)
        if (not prog.statements):
            show_message(this.window, "The file does not appear to be a gcode script")
            return

        if (prog.invalidLines):
            # Warn the user about the invalid lines (only show the first few)
            n = 10
            txt = "\n".join(prog.invalidLines[:n])
            extra = len(prog.invalidLines)-n
            if (extra > 0):
                txt += "\n\n(and %d more)" % extra
            show_message(this.window, "The gcode file contains invalid lines:\n\n%s" % txt)

        # Display the program source code
        buf = this.programText.get_buffer()
        for statement in prog.statements:
            buf.insert_with_tags_by_name(buf.get_end_iter(), "%04d:" % (statement.lineNumber+1), "numbers")
            buf.insert(buf.get_end_iter(), "  %s\n" % statement.command)

        state = prog.start()
        while not state.finished:
            state.step()

        if (state.unknownCodes):
            # Warn the user about the unrecognized gcode commands (only show the first few)
            n = 10
            txt = "\n".join(state.unknownCodes[:n])
            extra = len(state.unknownCodes)-n
            if (extra > 0):
                txt += "\n\n(and %d more)" % extra

            show_message(this.window, "The following gcode commands were not understood and will be ignored:\n\n%s" % txt)

        if (state.get_run_length() == 0):
            show_message(this.window, "The file does not appear to be a valid gcode script.")

        rapidLength = 0
        for path in state.paths:
            if (isinstance(path, gcode.Line) and path.rapid):
                rapidLength += path.length
        #print "rapid length: %0.1f" % rapidLength

        this.timeAdjust.set_upper(state.get_run_length()+1)
        this.state = state
        this.renderArea.set_machine_state(state)
        this.set_status("Program loaded (%d instructions)" % len(prog.statements))
        this.update_status()
        # Set the default zoom
        this.zoom_default_cb()

    def set_status(this, msg):
        this.statusLabel.set_markup("<small>%s</small>" % msg)
        buf = this.programText.get_buffer()
        buf.remove_tag_by_name("highlight", buf.get_start_iter(), buf.get_end_iter())

        lineno = this.renderArea.get_current_path().statement.lineNumber
        start = buf.get_iter_at_line(lineno)
        buf.apply_tag_by_name("highlight", start, buf.get_iter_at_line(lineno+1))
        this.programText.scroll_to_iter(start, 0.2, False, 0.5, 0.5)

    def build_menu(this):
        # Build the menu bar
        menu = Gtk.Toolbar()
        menu.show()

        # The open button
        item = Gtk.ToolButton(Gtk.STOCK_OPEN)
        item.set_tooltip_text("Open a gcode file")
        item.connect("clicked", this.open_cb)
        item.show()
        menu.insert(item, -1)
        this.openButton = item

        # Separator
        item = Gtk.SeparatorToolItem()
        item.show()
        menu.insert(item, -1)

        # The play button
        item = Gtk.ToolButton(Gtk.STOCK_MEDIA_PLAY)
        item.set_tooltip_text("Play gcode simulation")
        item.connect("clicked", this.play_cb)
        item.show()
        menu.insert(item, -1)
        this.playButton = item

        # The stop button
        item = Gtk.ToolButton(Gtk.STOCK_MEDIA_STOP)
        item.set_tooltip_text("Stop simulation")
        item.connect("clicked", this.stop_cb)
        item.show()
        menu.insert(item, -1)
        this.stopButton = item

        # The rewind button
        item = Gtk.ToolButton(Gtk.STOCK_MEDIA_REWIND)
        item.set_tooltip_text("Reset simulation")
        item.connect("clicked", this.rewind_cb)
        item.show()
        menu.insert(item, -1)
        this.rewindButton = item

        # The fast forward button
        item = Gtk.ToolButton(Gtk.STOCK_MEDIA_FORWARD)
        item.set_tooltip_text("Jump to end")
        item.connect("clicked", this.forward_cb)
        item.show()
        menu.insert(item, -1)
        this.forwardButton = item

        # Separator
        item = Gtk.SeparatorToolItem()
        item.show()
        menu.insert(item, -1)

        # The zoom in button
        item = Gtk.ToolButton(Gtk.STOCK_ZOOM_IN)
        item.set_tooltip_text("Zoom in")
        item.connect("clicked", this.zoom_in_cb)
        item.show()
        menu.insert(item, -1)
        this.zoomInButton = item

        # The zoom out button
        item = Gtk.ToolButton(Gtk.STOCK_ZOOM_OUT)
        item.set_tooltip_text("Zoom out")
        item.connect("clicked", this.zoom_out_cb)
        item.show()
        menu.insert(item, -1)
        this.zoomOutButton = item

        # The zoom fit button
        item = Gtk.ToolButton(Gtk.STOCK_ZOOM_100)
        item.set_tooltip_text("Zoom all")
        item.connect("clicked", this.zoom_default_cb)
        item.show()
        menu.insert(item, -1)
        this.zoomFitButton = item

        # Separator
        item = Gtk.SeparatorToolItem()
        item.show()
        menu.insert(item, -1)

        # The help button
        item = Gtk.ToolButton(Gtk.STOCK_HELP)
        item.set_tooltip_text("About this program")
        item.connect("clicked", this.help_cb)
        item.show()
        menu.insert(item, -1)

        return menu

    # Updates the status (eg sensitivity) of various widgets based on the
    # program state.
    def update_status(this):
        b = (this.state is not None)
        this.playButton.set_sensitive(b)
        this.stopButton.set_sensitive(b)
        this.zoomInButton.set_sensitive(b)
        this.zoomOutButton.set_sensitive(b)
        this.zoomFitButton.set_sensitive(b)
        this.timeSlider.set_sensitive(b)
        this.rewindButton.set_sensitive(b)
        this.forwardButton.set_sensitive(b)
        this.programText.set_sensitive(b)

    #############
    # Callbacks #
    #############

    # Called when the user clicks on the play button
    def play_cb(this, *args):
        # Toggle the play status
        this.renderArea.set_playing(not this.renderArea.get_playing())

    def rewind_cb(this, *args):
        this.renderArea.set_playing(False)
        this.renderArea.set_time(0)

    def forward_cb(this, *args):
        this.renderArea.set_playing(False)
        this.renderArea.set_time(this.state.get_run_length())

    # Called when the user clicks stop
    def stop_cb(this, *args):
        this.renderArea.set_playing(False)
        #this.renderArea.set_time(0)

    # Called when the user moves around the time slider
    def time_slider_changed_cb(this, *args):
        tm = this.timeAdjust.get_value()
        this.renderArea.set_time(tm)

    # Called when the gcode render widget changes
    def time_changed_cb(this, *args):
        path = this.renderArea.get_current_path()
        if (path):
            this.set_status(path.statement.command)
        # Update the position of the slider
        this.timeAdjust.handler_block(this.sliderChangedID)
        this.timeAdjust.set_value(this.renderArea.get_time())
        this.timeAdjust.handler_unblock(this.sliderChangedID)
        # For some reason this needs to be updated manually - maybe because the
        # signal is blocked above?
        this.timeSlider.queue_draw()
        # Update the head coordinates too
        pos = this.renderArea.get_head_pos()
        if (pos is not None):
            this.coordsLabel.set_text("(%0.1f, %0.1f) (mm)" % (pos[0], pos[1]))

    # Called when the user clicks on the open icon
    def open_cb(this, *args):
        # Stop playback
        this.renderArea.set_playing(False)

        w = Gtk.FileChooserDialog("Open file...", this.window, buttons=("Open file", Gtk.ResponseType.OK))

        # Add a filter for gcode scripts
        flt = Gtk.FileFilter()
        flt.set_name("GCode scripts (*.ngc)")
        flt.add_pattern("*.ngc")
        w.add_filter(flt)

        # Add a filter for everything else
        flt = Gtk.FileFilter()
        flt.set_name("All files")
        flt.add_pattern("*")
        w.add_filter(flt)

        ret = w.run()
        if (ret == Gtk.ResponseType.OK):
            this.load_program(w.get_filename())

        w.destroy()

    def zoom_in_cb(this, *args):
        zoom = min(this.renderArea.get_zoom()+0.2, 3)
        this.renderArea.set_zoom(zoom)

    def zoom_out_cb(this, *args):
        zoom = max(this.renderArea.get_zoom()-0.2, 0.2)
        this.renderArea.set_zoom(zoom)

    def zoom_default_cb(this, *args):
        # Calculate the zoom level so that everything fits on the screen
        (dx, dy) = this.renderArea.get_render_size()

        w = this.renderArea.get_allocated_width()
        h = this.renderArea.get_allocated_height()
        zoom = min(w/float(dx), h/float(dy))

        this.renderArea.set_zoom(zoom)
        # Center the view
        this.renderArea.set_view_pos((0,0))

    def mouse_button_cb(this, w, event):
        if (event.button == 1):
            if (event.type == Gdk.EventType.BUTTON_PRESS):
                # Start dragging around the render area when the user clicks
                # the left mouse button.
                this.dragging = True
                # Make note of where the mouse started dragging on the canvas
                this.dragMouseStart = (event.x, event.y)
                # Note where the render view was positioned
                this.dragStart = this.renderArea.get_view_pos()
            else:
                # Stop dragging
                this.dragging = False

    def mouse_motion_cb(this, w, event):
        if (this.dragging and this.dragMouseStart):
            # Calculate how far the user has moved the mouse since they
            # started dragging the canvas.
            dx = event.x - this.dragMouseStart[0]
            dy = event.y - this.dragMouseStart[1]
            # Reposition the render view
            this.renderArea.set_view_pos((
                this.dragStart[0] + dx,
                this.dragStart[1] + dy))

    def help_cb(this, *args):
        show_message(this.window, """Python G-Code Simulator
Version %s

Copyright Peter Rogers 2011
(peter.rogers@gmail.com)

Source licensed under GPL v2
See http://www.gnu.org/licenses/gpl-2.0.html""" % VERSION)

########
# Main #
########

def main():
    w = MainWindow()
    try:
        path = sys.argv[1]
    except IndexError:
        pass
    else:
        w.load_program(path)

    Gtk.main()

if (__name__ == "__main__"):
    main()


