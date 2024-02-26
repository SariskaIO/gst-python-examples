#!/usr/bin/env python3

import sys
import gi
import logging
from threading import Thread, Event
gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
from gi.repository import GLib, GObject, Gst

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("main")

def add_video_sources(pipe, loop):
    log.info("Adding videotestsrcs")
    # Create Sources
    srcs = [Gst.ElementFactory.make("videotestsrc") for _ in range(4)]

    sink = Gst.ElementFactory.make("autovideosink", "autovideosink")

    pipe.add(sink)
    log.info("Adding compositor")
    compositor = Gst.ElementFactory.make("compositor", "compositor")
    # Add elements to the pipeline
    [pipe.add(src) for src in srcs]  
    pipe.add(compositor)

    # Request pads from the compositor
    pads = [compositor.get_request_pad(f'sink_{i}') for i in range(4)]
    # Set properties for the pads to control the layout
    pad_properties = [(0, 0), (320, 0), (0, 320), (320, 320)]
    [pads[i].set_property('xpos', x) for i, (x, _) in enumerate(pad_properties)]
    [pads[i].set_property('ypos', y) for i, (_, y) in enumerate(pad_properties)]
    [pad.set_property('width', 320) for pad in pads]
    [pad.set_property('height', 320) for pad in pads]

   # Get the source pads
    for i, src in enumerate(srcs):
        srcpad = src.get_static_pad("src")
        srcpad.link(pads[i])

    # Link the sources to the compositor
    [src.link(compositor) for src in srcs]

    # Link the compositor to the sink
    compositor.link(sink)

    pipe.set_state(Gst.State.PLAYING)

    log.info("Waiting for a while before removing one source")
    GLib.timeout_add_seconds(5, remove_video_source, pipe, srcs[3], pads[3], compositor)

def remove_video_source(pipe, src, pad2, compositor):   
    log.debug(src.set_state(Gst.State.NULL))  # (5)
    log.debug(pipe.remove(src))
    log.debug(compositor.release_request_pad(pad2))  # (6)
    sink_pad = compositor.get_static_pad("sink_2")
    sink_pad.set_property('xpos', 160)
    sink_pad.set_property('ypos', 320)

    

def add_new_video_source(pipe, compositor):
    pipe.set_state(Gst.State.PAUSED)
    src = Gst.ElementFactory.make("videotestsrc")
    pipe.add(src)
    srcpad = src.get_static_pad("src")
    sink_pad = compositor.get_request_pad(f'sink_2')
    sink_pad.set_property('xpos', 0)
    sink_pad.set_property('ypos', 320)
    sink_pad.set_property('width', 320)
    sink_pad.set_property('height', 320)
    srcpad.link(sink_pad)
    src.link(compositor)
    pipe.set_state(Gst.State.PLAYING)
    print("Nothing")


def main(args):
    GObject.threads_init()
    Gst.init(None)

    global compositor  # Make compositor a global variable so that it can be accessed in remove_video_source
    compositor = Gst.ElementFactory.make("compositor", "compositor")

    pipe = Gst.Pipeline.new("dynamic")
    loop = GObject.MainLoop()

    add_video_sources(pipe, loop)

    try:
        loop.run()
    except:
        pass

    # cleanup
    pipe.set_state(Gst.State.NULL)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
