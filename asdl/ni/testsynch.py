"""Make test runs to asses the delay in synchronized tasks."""


def run_test(device_name, input_channel, output_channel,
             number_of_runs=10, samp_rate=51200, ):
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

    NOTES:
    - The read and write tasks use voltage channels.
    - Minimum and maximum values for writing and reading are -/+3.5 and
      -/+10.0 volts, respectively.

    """

    import nidaqmx
    from . import Task

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
            print(f'\rRun {i+1}/{number_of_runs} ... ',
                  file=sys.stderr, flush=True, end='')

            task.write_task.write(data_out, auto_start=False)
            task.synchronize()

            data_in[:, i] = task.read_task.read(nsamples)

            task.stop()

        print(f'done', file=sys.stderr, flush=True)

    return (product_type, data_out, data_in)


def _make_arg_parser():
    import argparse

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

    import time
    import sys
    import numpy as np

    product_type, data_out, data_in = \
        run_test(args.device, args.input_channel, args.output_channel,
                 int(args.runs), float(args.rate))

    # Output
    header = f"""Date: {time.strftime("%a, %d %b %Y %H:%M:%S %z", time.localtime())}
Product: {product_type}
Sampling rate: {float(args.rate)}
Number of runs: {int(args.runs)}"""

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

    if args.plot:
        import matplotlib.pyplot as plt

        plt.plot(data_out, label='Generated data')
        plt.plot(data_in[:, -1], label='Measured signal')
        plt.legend()
        plt.title(f"Last run: #{args.runs}")
        plt.xlabel('Sample number')
        plt.ylabel('Amplitude')
        plt.grid(True)
        plt.show()

