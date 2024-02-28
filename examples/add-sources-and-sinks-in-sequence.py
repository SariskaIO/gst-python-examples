#!/usr/bin/env python3

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
    return Gst.ElementFactory.make("videotestsrc", f'src+{participant_num}')

def get_sink():
    return Gst.ElementFactory.make("autovideosink", "autovideosink")

def get_compositor():
    return Gst.ElementFactory.make("compositor", "compositor")

def add_video_source(participant_num):
    log.info(f"Adding videotestsrc for participant {participant_num}")
    src = get_source(participant_num)
    pipeline.add(src)
    participants.append(src)

    num_cols = 2  # Number of columns in the grid
    row = participant_num // num_cols
    col = participant_num % num_cols

    pad = compositor.get_request_pad(f'sink_{participant_num}')
    pad.set_property('xpos', 320 * col)
    pad.set_property('ypos', 320 * row)
    pad.set_property('width', 320)
    pad.set_property('height', 320)

    srcpad = src.get_static_pad("src")
    srcpad.link(pad)

    src.link(compositor)
    pipeline.set_state(Gst.State.PLAYING)

def remove_participant():
    if participants:
        participant_to_remove = random.choice(participants)
        participants.remove(participant_to_remove)

        # Get the participant number from the source name
        participant_num = int(participant_to_remove.get_name().split('+')[-1])

        print(f"Removing participant {participant_num}")
        
        remove_pad = compositor.get_static_pad(f'sink_{participant_num}')
        compositor.release_request_pad(remove_pad)

        # Re-adjust the positions of the remaining participants
        for i, participant in enumerate(participants):
            participant_num = int(participant.get_name().split('+')[-1])
            num_cols = 2
            row = i // num_cols
            col = i % num_cols

            pad = compositor.get_static_pad(f'sink_{participant_num}')
            pad.set_property('xpos', 320 * col)
            pad.set_property('ypos', 320 * row)

        pipeline.set_state(Gst.State.PLAYING)

def add_participants(total_participants, current_participant):
    if current_participant < total_participants:
        add_video_source(current_participant)
        current_participant += 1

        # Schedule adding the next participant after 5 seconds
        GLib.timeout_add_seconds(2, add_participants, total_participants, current_participant)

def main(args):
    global compositor, sink, pipeline

    GObject.threads_init()
    Gst.init(None)

    pipeline = Gst.Pipeline.new("dynamic")
    loop = GObject.MainLoop()

    compositor = get_compositor()
    pipeline.add(compositor)

    sink = get_sink()
    pipeline.add(sink)

    total_participants = 8
    current_participant = 0

    add_participants(total_participants, current_participant)

    compositor.link(sink)

    pipeline.set_state(Gst.State.PLAYING)

    # Schedule removing a participant randomly every 10 seconds
    GLib.timeout_add_seconds(25, remove_participant)

    try:
        loop.run()
    except:
        pass

    # cleanup
    pipeline.set_state(Gst.State.NULL)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
