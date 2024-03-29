#!/usr/bin/env python3

'''
Simple example to demonstrate dynamically adding and removing source elements
to a playing pipeline.

This particular example uses videotestsrc elements and a compositor to display the source twice
'''

import sys
import random

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
from gi.repository import GLib, GObject, Gst


# Define a class to hold data for dynamic source management
class ProbeData:
    def __init__(self, pipe, src):
        self.pipe = pipe
        self.src = src

# Callback function to handle bus messages
def bus_call(bus, message, loop):
    t = message.type
    if t == Gst.MessageType.EOS:
        sys.stdout.write("End-of-stream\n")
        loop.quit()
    elif t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        sys.stderr.write("Error: %s: %s\n" % (err, debug))
        loop.quit()
    return True

# Callback function to dispose of the source element
def dispose_src_cb(src):
    src.set_state(Gst.State.NULL)

# Callback function for pad probe
def probe_cb(pad, info, pdata):
    peer = pad.get_peer()
    pad.unlink(peer)
    pdata.pipe.remove(pdata.src)
    # Can't set the state of the src to NULL from its streaming thread
    GLib.idle_add(dispose_src_cb, pdata.src)

    pdata.src = Gst.ElementFactory.make('videotestsrc')
    pdata.src.props.pattern = random.randint(0, 24)
    pdata.pipe.add(pdata.src)
    srcpad = pdata.src.get_static_pad ("src")
    srcpad.link(peer)
    pdata.src.sync_state_with_parent()

    GLib.timeout_add_seconds(1, timeout_cb, pdata)

    return Gst.PadProbeReturn.REMOVE

# Callback function for timeout
def timeout_cb(pdata):
    srcpad = pdata.src.get_static_pad('src')
    srcpad.add_probe(Gst.PadProbeType.IDLE, probe_cb, pdata)
    return GLib.SOURCE_REMOVE

# Main function
def main(args):
    Gst.init(None)

    # Create pipeline and elements
    pipe = Gst.Pipeline.new('dynamic')
    src1 = Gst.ElementFactory.make('videotestsrc')
    src2 = Gst.ElementFactory.make('videotestsrc')
    compositor = Gst.ElementFactory.make('compositor')
    sink = Gst.ElementFactory.make('autovideosink')
    
    # Add elements to the pipeline
    pipe.add(src1)
    pipe.add(src2)
    pipe.add(compositor)
    pipe.add(sink)

    # Request pads from the compositor
    pad1 = compositor.get_request_pad('sink_%u')
    pad2 = compositor.get_request_pad('sink_%u')


    # Set properties for the pads to control the layout
    pad1.set_property('xpos', 0)  # position of src1

    # Get the width of pad1
    pad2.set_property('xpos', 320)  # position of src2

    # Get the source pads
    srcpad1 = src1.get_static_pad("src")
    srcpad2 = src2.get_static_pad("src")

    # Link the source pads to the requested pads of the compositor
    srcpad1.link(pad1)
    srcpad2.link(pad2)

    # Link the sources to the compositor
    src1.link(compositor)
    src2.link(compositor)

    # Link the compositor to the sink
    compositor.link(sink)

    # Initialize ProbeData objects for dynamic source management
    pdata1 = ProbeData(pipe, src1)
    pdata2 = ProbeData(pipe, src2)

    # Create a main loop
    loop = GObject.MainLoop()

    # Add timeout callbacks for dynamic source management
    GLib.timeout_add_seconds(20, timeout_cb, pdata1)
    GLib.timeout_add_seconds(20, timeout_cb, pdata2)

    # Setup bus to handle messages
    bus = pipe.get_bus()
    bus.add_signal_watch()
    bus.connect ("message", bus_call, loop)
    
    # Start playback and listen to events
    pipe.set_state(Gst.State.PLAYING)
    try:
        loop.run()
    except:
        pass
    
    # Cleanup
    pipe.set_state(Gst.State.NULL)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
