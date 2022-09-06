"""Read and write data using one single NI device.

This example uses `SingleDevice` class to manage a read and a write
task, which are configured independently:
- The writing task outputs a signal continuously, non-stop.
- The reading task reads only the data that it needs to read.

When a read task is set to continuously read data, it expects the
computer to read data and free its internal memory at an appropriate
rate.  If the device's memory cannot hold any more samples, an error
is thrown and the application crashes.  Since we cannot guarantee that
the computer will read everything in time, the solution is to set only
the write task to CONTINUOUS, and set the reading task to FINITE,
which means that the reading buffer will certainly be empty after each
`read` command.

"""

from asdl.ni import *
import matplotlib.pyplot as plt
import nidaqmx as ni
import numpy as np
import sys


def update_graph(figure, line, new_values):
    """Update a 'line' in a 'figure' using 'new_values'."""
    line.set_ydata(new_values)
    figure.canvas.draw()
    figure.canvas.flush_events()


# Sampling parameters and variable to hold data
nsamples = 500                  # Number of samples
sampl_rate = 100e3              # Sampling rate (samples/s)
ts = np.arange(nsamples) * 1/sampl_rate
data_out = np.sin(2 * np.pi * 100e3 * ts)
data_in = np.zeros((nsamples,))

# Prepare plotting
plt.ion()
fig = plt.figure(1)
fig.canvas.manager.set_window_title('Reading data')
ax = fig.add_subplot(1, 1, 1)
line, = ax.plot(data_in)
ax.set_ylim((-10,10))
ax.set_xlim((0, nsamples))
ax.set_title('Input signal')
ax.set_xlabel('Sample')
ax.set_ylabel('Voltage (V)')
ax.grid()

with SingleDevice('Dev6') as task:
    task.add_ai_voltage_chan(
        'Dev6/ai0',
        min_val=-1,
        max_val=+1)
    task.add_ao_voltage_chan(
        'Dev6/ao0',
        min_val=-1,
        max_val=+1)
    # Do not use `cfg_samp_clk_timing` because it configures both
    # read and write tasks simultaneously.  Instead, use
    # `timing.cfg_sampl_clk_timing` for each task individually.
    task.write_task.timing.cfg_samp_clk_timing(
        sampl_rate,
        # Set to CONTINUOUS to no interrupt the output.
        sample_mode=ni.constants.AcquisitionType.CONTINUOUS,
        samps_per_chan=nsamples,
    )
    task.read_task.timing.cfg_samp_clk_timing(
        sampl_rate,
        # Set to FINITE to read only the samples we need.
        sample_mode=ni.constants.AcquisitionType.FINITE,
        samps_per_chan=nsamples,
    )
    task.write_task.write(data_out, auto_start=False)
    task.synchronize()
    print('Writing and reading data ... press Ctrl-C to exit.',
          file=sys.stderr,
          flush=True,
          )
    try:
        while True:
            data_in = task.read_task.read(
                number_of_samples_per_channel=nsamples)
            update_graph(fig, line, data_in)
    except KeyboardInterrupt:
        print('Done.', file=sys.stderr)
