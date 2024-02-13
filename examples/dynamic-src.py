#!/usr/bin/env python3

'''
Simple example to demonstrate dynamically adding and removing source elements
to a playing pipeline.
'''

import sys
import random

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
from gi.repository import GLib, GObject, Gst

class ProbeData:
    def __init__(self, pipe, src):
        self.pipe = pipe
        self.src = src

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

def dispose_src_cb(src):
    src.set_state(Gst.State.NULL)

# def probe_cb(pad, info, pdata):
#     peer = pad.get_peer()
#     pad.unlink(peer)
#     pdata.pipe.remove(pdata.src)
#     # Can't set the state of the src to NULL from its streaming thread
#     GLib.idle_add(dispose_src_cb, pdata.src)

#     pdata.src = Gst.ElementFactory.make('videotestsrc')
#     pdata.src.props.pattern = random.randint(0, 24)

#     pdata.pipe.add(pdata.src)

#     srcpad = pdata.src.get_static_pad ("src")

#     srcpad.link(peer)

#     pdata.src.sync_state_with_parent()

#     GLib.timeout_add_seconds(10, timeout_cb, pdata)
#     return Gst.PadProbeReturn.REMOVE
    
def probe_cb(pad, info, pdata):
    # Ensure peer pad is valid before linking
    peer = pad.get_peer()
    if not peer:
        print("WARNING: peer pad not available, skipping linking")
        return Gst.PadProbeReturn.REMOVE

    # Pause pipeline before modifications (consider if necessary)
    pdata.pipe.set_state(Gst.State.PAUSED)

    # Unlink pads
    pad.unlink(peer)

    # Remove old source element
    pdata.pipe.remove(pdata.src)
    print("Removing old source element")
    GLib.idle_add(dispose_src_cb, pdata.src)

    # Create new videotestsrc element
    print("Creating new source element")
    new_src = Gst.ElementFactory.make('videotestsrc')
    new_src.props.pattern = random.randint(0, 24)

    # Add new source element (ensure it's added before linking)
    pdata.pipe.add(new_src)

    # Sync state of new source with pipeline
    new_src.sync_state_with_parent()

    # Get and link source pad
    new_srcpad = new_src.get_static_pad("src")
    new_srcpad.link(peer)

    # Sync peer pad state if added dynamically
    if not peer.get_parent():
        peer.sync_state_with_parent()

    # Update pdata and play
    pdata.src = new_src
    pdata.pipe.set_state(Gst.State.PLAYING)  # Consider resuming if paused earlier

    # Schedule timeout callback
    GLib.timeout_add_seconds(10, timeout_cb, pdata)

    return Gst.PadProbeReturn.REMOVE


def timeout_cb(pdata):
    srcpad = pdata.src.get_static_pad('src')
    srcpad.add_probe(Gst.PadProbeType.IDLE, probe_cb, pdata)
    return GLib.SOURCE_REMOVE

def main(args):
    GObject.threads_init()
    Gst.init(None)

    pipe = Gst.Pipeline.new('dynamic')
    src = Gst.ElementFactory.make('videotestsrc')

    sink = Gst.ElementFactory.make('autovideosink')
    pipe.add(src)
    pipe.add(sink)
    src.link(sink)

    pdata = ProbeData(pipe, src)

    loop = GObject.MainLoop()

    GLib.timeout_add_seconds(5, timeout_cb, pdata)

    bus = pipe.get_bus()
    bus.add_signal_watch()
    bus.connect ("message", bus_call, loop)
    
    # start play back and listen to events
    pipe.set_state(Gst.State.PLAYING)
    try:
      loop.run()
    except:
      pass
    
    # cleanup
    pipe.set_state(Gst.State.NULL)

if __name__ == '__main__':
    sys.exit(main(sys.argv))