"""Make test runs to asses the delay in synchronized tasks."""

from . import Task
import argparse
import nidaqmx
import numpy as np
import sys
import time


def run_test(device_name, input_channel, output_channel,
             number_of_runs=10, samp_rates=[51200], quiet_flag=True):
    """Run tests assess the delay in synchronized tasks.

    Configure and synchronize two tasks to assess the delay between
    the start of a reading task and start of a writing task.  It
    writes a step function to `output_channel` in which the first
    sample is 0 and all subsequent ones are 1, and read the result
    from `input_channel`.  Both channels should be in the same device
    named `device_name`.

    Returns a dict with a keys 'product_type' and the sampling rates:
    - 'product_type' contains the type of the device, e.g. 'USB-4431', and
    - sampling rates key contain a tuple `(data_out, data_in)`, where
      `data_out` is the data written to the device, and `data_in` is
      the signal read from it.  Both `data_out` and `data_in` are
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
    samp_rates: list, optional, default: [51200]
        A list of the sampling rate of the tasks in samples/second.
    quiet_flag: bool, optional, default: True
        Control the display of messages of progress that are sent to
        `stderr`.

    NOTES:
    - The read and write tasks use voltage channels.
    - Minimum and maximum values for writing and reading are -/+3.5 and
      -/+10.0 volts, respectively.

    """
    devices = nidaqmx.system.System.local().devices
    try:
        device = devices[device_name]
    except KeyError:
        raise ValueError(f'device not found: {device_name}')

    results = {'product_type': f'{device.product_type}'}

    with Task() as task:
        task.write_task.ao_channels.add_ao_voltage_chan(
            f'{device_name}/{output_channel}',
            min_val=-3.5, max_val=3.5)
        task.read_task.ai_channels.add_ai_voltage_chan(
            f'{device_name}/{input_channel}',
            min_val=-10, max_val=10)

        # Try all sampling rates before the actual runs
        # Because `nidaqmx` error messages are very informative,
        # don't try and catch, keep calm and let it crash
        for samp_rate in samp_rates:
            # Use continuous acquisition to avoid warnings from nidaqmx
            task.cfg_samp_clk_timing(samp_rate, samps_per_chan=5, \
                sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS)

            # Seems like NI USB-4463 does not synchronize if there is
            # nothing to write, and it also does not check invalid
            # sampling rate before synchronizing, so let us include
            # these next two statements
            task.write_task.write(np.ones((5,)), auto_start=False)
            task.synchronize()
            task.stop()

        # Actual runs
        for samp_rate in samp_rates:
            data_out = np.ones((int(samp_rate,)))
            data_out[0] = 0
            nsamples = len(data_out)
            task.cfg_samp_clk_timing(samp_rate, samps_per_chan=nsamples)

            data_in = np.empty((nsamples, number_of_runs))
            for i in range(number_of_runs):
                task.write_task.write(data_out, auto_start=False)
                task.synchronize()

                if not quiet_flag:
                    print(f'\rRun {i+1}/{number_of_runs} @ {samp_rate} \
samples/second ... ', file=sys.stderr, flush=True, end='')

                data_in[:, i] = task.read_task.read(nsamples)

                task.stop()

            if not quiet_flag:
                print(f'done', file=sys.stderr, flush=True)

            results[samp_rate] = (data_out, data_in)

    return results


def analyze_results(data_out, data_in):
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
        min_val, max_val = np.min(data[:, j]), np.max(data[:, j])
        signal = data[:, j] > (max_val - min_val) / 2 + min_val
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

    return results


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('device', help='the name of the device',)
    arg_parser.add_argument('input_channel', help='name of the input channel')
    arg_parser.add_argument('output_channel', help='name of the output channel')
    arg_parser.add_argument('-a', '--analysis', help='analyze the results',
                        action='store_true')
    arg_parser.add_argument('-q', '--quiet',
                       help='suppress messages of progress of the task',
                       action='store_true')
    arg_parser.add_argument('--file',
                        help="save the data to a CSV file; \
default is the product type of the device, e.g. 'USB-4431.csv; \
if FILE is '-' send results to standard output instead")
    arg_parser.add_argument('--runs',
                        help='number of test runs; defualt is 10',
                        type=int,
                        default=10)
    arg_parser.add_argument('--rate',
                        help='sampling rate in samples/second; \
default is 51200; can be a list of space-separated values',
                        type=int,
                        nargs='+',
                        default=[51200])
    args = arg_parser.parse_args()

    run_results = run_test(args.device, args.input_channel,
                            args.output_channel, args.runs,
                            args.rate, args.quiet)

    header = f"""Date: {time.strftime("%a, %d %b %Y %H:%M:%S %z", time.localtime())}
Product: {run_results['product_type']}
Sampling rates (samples/second): {args.rate}
Number of runs per sampling rate: {args.runs}"""

    analysis_header = {'avg': [], 'std': [], 'max': [], 'min': []}

    nsamples = int(np.min(args.rate))
    values = np.zeros((nsamples, args.runs * len(args.rate) + 1))
    values_header = []

    for i, (rate, (data_out, data_in)) \
        in enumerate(kv for kv in run_results.items()
                     if kv[0] != 'product_type'):

        for j in range(1, args.runs + 1):
            values_header.append(f'{{rate={rate},run={j}}}')

        if args.analysis:
            analysis_results = analyze_results(data_out, data_in)
            for key, value in (kv for kv in analysis_results.items()
                               if kv[0] != 'edges'):
                analysis_header[key].append(value)

        if data_out.size == nsamples:
            values_header.insert(0, '{rate=0,run=0}')
            values[:, 0] = data_out

        values[:, i*args.runs + 1 : (i+1)*args.runs + 1] = data_in[:nsamples, :]

    if args.analysis:
        header += f"""
Average (samples): {analysis_header['avg']}
Standard deviation (samples): {analysis_header['std']}
Minimum delay (samples): {analysis_header['min']}
Maximum delay (samples): {analysis_header['max']}"""

    header += '\n' + ' '.join(values_header)

    if args.file == '-':
        file_name = sys.stdout
    elif args.file is None:
        file_name = run_results['product_type'] + '.csv'
    else:
        file_name = args.file

    np.savetxt(file_name, values, header=header)
