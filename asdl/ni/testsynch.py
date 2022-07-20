"""Make test runs to asses the delay in synchronized tasks."""

from . import Task
import argparse
import nidaqmx
import matplotlib.pyplot as plt
import numpy as np
import sys
import time


def run_test(device_name, input_channel, output_channel,
             number_of_runs=10, samp_rate=51200, quiet_flag=True):
    """Run tests assess the delay in synchronized tasks.

    Configure and synchronize two tasks to assess the delay between
    the start of a reading task and start of a writing task.  It
    writes a step function to `output_channel` in which the first
    sample is 0 and all subsequent ones are 1, and read the result
    from `input_channel`.  Both channels should be in the same device
    named `device_name`.

    Returns a tuple `(product_type, data_out, data_in)`, where
    `product_type` is the type of the device, e.g. 'USB-4431',
    `data_out` is the data written to the device, and `data_in` is the
    signal read from it.  Both `data_out` and `data_in` are
    `numpy.ndarray` whose shapes are (round(samp_rate),) and
    (round(samp_rate), number_of_runs), respectively. '.

    Parameters:
    device_name: string
        The name of the device.
    input_channel: string
        The name of the input channel.
    output_channel: string
        The name of the output channel.
    number_of_runs: int, optional, default: 10
        Number of time the test should be repeated.
    samp_rate: float, optional, default: 51200
        The sampling rate of the tasks in samples/second.
    quiet_flag: bool, optional, default: True
        Control the display of messages of progress that are sent to
        `stderr`.

    NOTES:
    - The read and write tasks use voltage channels.
    - Minimum and maximum values for writing and reading are -/+3.5 and
      -/+10.0 volts, respectively.

    """
    # Generate enough data for 1 second of acquisition
    data_out = np.ones((int(samp_rate,)))
    data_out[0] = 0
    nsamples = len(data_out)

    devices = nidaqmx.system.System.local().devices
    try:
        device = devices[device_name]
    except KeyError:
        raise ValueError(f'device not found: {device_name}')

    product_type = f'{device.product_type}'

    with Task() as task:
        task.write_task.ao_channels.add_ao_voltage_chan(
            f'{device_name}/{output_channel}',
            min_val=-3.5, max_val=3.5)
        task.read_task.ai_channels.add_ai_voltage_chan(
            f'{device_name}/{input_channel}',
            min_val=-10, max_val=10)
        task.cfg_samp_clk_timing(samp_rate, samps_per_chan=nsamples)

        data_in = np.empty((nsamples, number_of_runs))

        for i in range(number_of_runs):
            if not quiet_flag:
                print(f'\rRun {i+1}/{number_of_runs} ... ',
                      file=sys.stderr, flush=True, end='')

            task.write_task.write(data_out, auto_start=False)
            task.synchronize()

            data_in[:, i] = task.read_task.read(nsamples)

            task.stop()

        if not quiet_flag:
            print(f'done', file=sys.stderr, flush=True)

    return (product_type, data_out, data_in)


def analyze_results(data_out, data_in, plot_flag=False):
    """Analyze the results of the tests.

    It detects the position of the rising edges in `data_in` and
    `data_out`, takes the difference between them and calculates a few
    statistical informations.

    Returns a dictionary whose fields and values are:
    - 'avg': a float, the average,
    - 'max': a int, the maximum value,
    - 'min': a int, the minimum value,
    - 'std': a float, the standard deviation
    - 'edges': a 1D numpy.ndarray, the positions of the edges for
      `data_out` and `data_in`, in this order.

    Parameters:
    data_out: 1D numpy.ndarray
        The data written to the device which will be used as
        reference.  Should be of shape (N,).
    data_in: 2D numpy.ndarray
        The data read from the device.  Should be of shape
        (N,M).
    plot_flag: bool, optional, default: False
        Controls the plotting of the results.  If True, plots a
        histogram for the results.

    """
    # Detecting edges
    data = np.hstack((np.expand_dims(data_out, 1), data_in))
    nrows, ncols = data.shape
    edges = np.zeros((ncols,), dtype=int)
    for j in range(ncols):
        signal = data[:, j] > 0.5
        for i in range(nrows - 1):
            if (not signal[i]) and signal[i+1]:
                edges[j] = i + 1
                break
    delta = edges[1:] - edges[0]
    results = {'avg': np.average(delta),
               'max': np.max(delta),
               'min': np.min(delta),
               'std': np.std(delta),
               'edges': edges}

    if plot_flag:
        plt.figure()
        plt.hist(delta, density=True)
        plt.xlabel('Delay (samples)')
        plt.ylabel('Frequency')
        plt.title('Frequency distribution of the delay between read and write tasks')

    return results


def _make_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('device', help='the name of the device',)
    parser.add_argument('input_channel', help='name of the input channel')
    parser.add_argument('output_channel', help='name of the output channel')

    parser.add_argument('-a', '--analysis', help='analyze the results',
                        action='store_true')

    parser.add_argument('-p', '--plot',
                        help="plot results for the last run. \
If '-a' is also passed, plot a histogram too.",
                        action='store_true')

    parser.add_argument('-q', '--quiet',
                       help='suppress messages of progress of the task',
                       action='store_true')

    parser.add_argument('--file',
                        help="save the data to a CSV file; \
default is the product type of the device, e.g. 'USB-4431.csv; \
if FILE is '-' send results to standard output instead")

    parser.add_argument('--runs',
                        help='number of test runs; defualt is 10',
                        type=int,
                        default=10)

    parser.add_argument('--rate',
                        help='sampling rate in samples/second; \
default is 51200',
                        type=float,
                        default=51200.0)
    return parser


if __name__ == '__main__':
    # Try parsing args before loading everything else
    arg_parser = _make_arg_parser()
    args = arg_parser.parse_args()

    product_type, data_out, data_in = \
        run_test(args.device, args.input_channel, args.output_channel,
                 int(args.runs), float(args.rate), args.quiet)

    header = f"""Date: {time.strftime("%a, %d %b %Y %H:%M:%S %z", time.localtime())}
Product: {product_type}
Sampling rate (samples/second): {float(args.rate)}
Number of runs: {int(args.runs)}"""

    if args.plot:
        plt.plot(data_out, label='Generated data')
        plt.plot(data_in[:, -1], label='Measured signal')
        plt.legend()
        plt.title(f"Last run: #{args.runs}")
        plt.xlabel('Sample number')
        plt.ylabel('Amplitude')
        plt.grid(True)

    if args.analysis:
        results = analyze_results(data_out, data_in, args.plot)
        header += f"""
Average (samples): {results['avg']}
Standard deviation (samples): {results['std']}
Maximum delay (samples): {results['max']}
Minimum delay (samples): {results['min']}"""

    if args.plot:
        # Because the analysis may also create a plot, wait until
        # after it to call plt.show
        plt.show()

    if args.file == '-':
        file_name = sys.stdout
    elif args.file is None:
        file_name = product_type + '.csv'
    else:
        file_name = args.file

    np.savetxt(file_name,
               np.hstack((np.expand_dims(data_out, 1), data_in)),
               delimiter=',',
               header=header)
