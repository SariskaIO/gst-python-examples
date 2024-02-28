#!/usr/bin/env python3

"""
Dynamic GStreamer pipeline with participants in a grid.

This script creates a GStreamer pipeline that dynamically adds and removes video sources
(simulating participants) arranged in a grid using the compositor element.

Usage:
- Change the number of columns in the grid: Modify the 'num_cols' variable in the add_video_source function.
- Change the total number of participants: Modify the 'total_participants' variable in the main function.

Requirements:
- GStreamer and the necessary Python bindings (gi.repository) must be installed.

"""

import sys
import gi
import logging
import random
gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
from gi.repository import GLib, GObject, Gst

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("main")

compositor = None
sink = None
pipeline = None
participants = []

def get_source(participant_num):
    """Create and return a videotestsrc element for a participant."""
    return Gst.ElementFactory.make("videotestsrc", f'src+{participant_num}')

def get_sink():
    """Create and return an autovideosink element for the final output."""
    return Gst.ElementFactory.make("autovideosink", "autovideosink")

def get_compositor():
    """Create and return a compositor element for arranging video sources."""
    return Gst.ElementFactory.make("compositor", "compositor")

def add_video_source(participant_num):
    """Add a video source (participant) to the pipeline."""
    log.info(f"Adding videotestsrc for participant {participant_num}")
    src = get_source(participant_num)
    pipeline.add(src)
    participants.append(src)

    num_cols = 4  # Number of columns in the grid
    row = participant_num // num_cols
    col = participant_num % num_cols

    # Request a sink pad from the compositor and set its properties
    pad = compositor.get_request_pad(f'sink_{participant_num}')
    pad.set_property('xpos', 320 * col)
    pad.set_property('ypos', 320 * row)
    pad.set_property('width', 320)
    pad.set_property('height', 320)

    # Link the source pad to the requested sink pad on the compositor
    srcpad = src.get_static_pad("src")
    srcpad.link(pad)

    # Link the source to the compositor
    src.link(compositor)

    # Set the pipeline to PLAYING state
    pipeline.set_state(Gst.State.PLAYING)

def remove_sink_pad():
    """Remove a random participant's sink pad from the compositor."""
    if participants:
        participant_to_remove = random.choice(participants)
        participants.remove(participant_to_remove)

        # Get the participant number from the source name
        participant_num = int(participant_to_remove.get_name().split('+')[-1])

        print(f"Removing participant {participant_num}")

        # Release the request pad from the compositor
        remove_pad = compositor.get_static_pad(f'sink_{participant_num}')
        compositor.release_request_pad(remove_pad)

        # Re-adjust the positions of the remaining participants on the grid
        for i, participant in enumerate(participants):
            participant_num = int(participant.get_name().split('+')[-1])
            num_cols = 4
            row = i // num_cols
            col = i % num_cols

            pad = compositor.get_static_pad(f'sink_{participant_num}')
            pad.set_property('xpos', 320 * col)
            pad.set_property('ypos', 320 * row)

        # Set the pipeline to PLAYING state
        pipeline.set_state(Gst.State.PLAYING)

def add_participants(total_participants, current_participant):
    """Add participants to the pipeline at intervals."""
    if current_participant < total_participants:
        add_video_source(current_participant)
        current_participant += 1

        # Schedule adding the next participant after 1 second
        GLib.timeout_add_seconds(1, add_participants, total_participants, current_participant)

def main(args):
    global compositor, sink, pipeline

    # Initialize GObject threads and GStreamer
    GObject.threads_init()
    Gst.init(None)

    # Create a new GStreamer pipeline and a main loop
    pipeline = Gst.Pipeline.new("dynamic")
    loop = GObject.MainLoop()

    # Create compositor and sink elements and add them to the pipeline
    compositor = get_compositor()
    pipeline.add(compositor)

    sink = get_sink()
    pipeline.add(sink)

    # Set the number of participants to be added
    total_participants = 9
    current_participant = 0

    # Add participants to the pipeline
    add_participants(total_participants, current_participant)

    # Link the compositor to the sink
    compositor.link(sink)

    # Set the pipeline to PLAYING state
    pipeline.set_state(Gst.State.PLAYING)

    # Schedule removing a participant randomly every 25 seconds
    GLib.timeout_add_seconds(25, remove_sink_pad)

    try:
        loop.run()
    except:
        pass

    # Cleanup: Set the pipeline to NULL state
    pipeline.set_state(Gst.State.NULL)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
