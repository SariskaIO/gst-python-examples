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
    GLib.timeout_add_seconds(10, remove_video_source, pipe, srcs[2], pads[2], compositor)

def remove_video_source(pipe, src, pad2, compositor):   
    log.debug(src.set_state(Gst.State.NULL))  # (5)
    log.debug(pipe.remove(src))
    log.debug(compositor.release_request_pad(pad2))  # (6)


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
