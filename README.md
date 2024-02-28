# gst-python-examples

This repository contains examples of GStreamer pipelines written in Python.

## Prerequisites

Make sure you have Python and GStreamer installed on your system. If you're using Ubuntu, you can install them with:

```bash
sudo apt-get install python3 python3-gst-1.0 gstreamer1.0-plugins-good
```

# Running the examples

The examples are located in the examples folder.

To run an example, navigate to the examples directory in your terminal and run the Python script with Python. For example, if you want to run example1.py, you would use:

```bash
cd examples
python example1.py
```

Replace example1.py with the name of the script you want to run.

Note: In case of helloworld.py, you'd need to pass the path to the file you want to play in the argument like this:

```bash
python helloworld.py ../assets/video.mp4
```

## Usage per examples

1. Ensure GStreamer is installed on your system.

2. Run the script using Python 3:

    ```bash
    python3 add-sources-and-sinks-in-sequence.py
    ```

3. Modify the script to customize the grid layout and total number of participants.

## Customization

- To change the number of columns in the grid, modify the `num_cols` variable in the `add_video_source` function.
  
- To change the total number of participants, modify the `total_participants` variable in the `main` function.

## Features

- **Dynamic Participants**: Participants are dynamically added and removed at runtime.

- **Grid Layout**: Video sources are arranged in a grid using the compositor element.

- **Real-time Adjustments**: The pipeline adapts in real-time to changes in the number of participants.


# Troubleshooting
If you encounter any issues, make sure you have the latest versions of Python and GStreamer installed. If the problem persists, please open an issue on GitHub.
