#!/usr/bin/env python3

'''
Simple example to demonstrate dynamically adding and removing source elements
to a playing pipeline.

This particular example uses videotestsrc elements and a compositor to display the source four times
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

    # Create a main loop
    loop = GLib.MainLoop()

        # Create pipeline and elements
    pipe = Gst.Pipeline.new('dynamic')
    srcs = [Gst.ElementFactory.make('videotestsrc') for _ in range(4)]
    compositor = Gst.ElementFactory.make('compositor')
    sink = Gst.ElementFactory.make('autovideosink')

    # Add elements to the pipeline
    [pipe.add(src) for src in srcs]  
    pipe.add(compositor)
    pipe.add(sink)

    # Request pads from the compositor
    pads = [compositor.get_request_pad(f'sink_{i}') for i in range(4)]

    # Set properties for the pads to control the layout
    pad_properties = [(0, 0), (320, 0), (0, 320), (320, 320)]
    [pads[i].set_property('xpos', x) for i, (x, _) in enumerate(pad_properties)]
    [pads[i].set_property('ypos', y) for i, (_, y) in enumerate(pad_properties)]

    # Get the source pads
    for i, src in enumerate(srcs):
        srcpad = src.get_static_pad("src")
        srcpad.link(pads[i])


    # Link the sources to the compositor
    [src.link(compositor) for src in srcs]

    # Link the compositor to the sink
    compositor.link(sink)

    # Initialize ProbeData objects for dynamic source management
    pdata = [ProbeData(pipe, src) for src in srcs]

    # Add timeout callbacks for dynamic source management
    [GLib.timeout_add_seconds(20, timeout_cb, data) for data in pdata]


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