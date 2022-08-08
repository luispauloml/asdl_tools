import cmd
import nidaqmx
import numpy as np
import functools
import traceback
import sys
from . import SingleDevice


class InteractiveExperiment(cmd.Cmd):
    """Interactive prompts for a task with single device."""
    intro = "Try '?' or 'help' for help."
    prompt = '(Interactive Experiment) '

    def emptyline(self):
        """Print nothing."""
        self.stdout.write('')

    def badinput(self, msg):
        """Print warning of bad input.

        Parameters:
        msg : str
            The string to be printed in the message.

        """
        self.stdout.write('*** Bad input: ' + msg + '\n')

    def setup(self):
        """Set up the system.

        This method does nothing unless it is overridden.

        """
        pass

    def do_setup(self, *args_):
        """Run the setup."""
        return self.setup()

    def do_variables(self, *args_):
        """List all variables that can be changed."""
        names = dir(self)
        var_names = [name[4:] for name in names if name.startswith('set_')]
        self.stdout.write('\nVariables:\n')
        if self.ruler:
            self.stdout.write(f'{self.ruler * 10}\n')
        if var_names  == []:
            self.stdout.write('*** No variables to be set\n')
        else:
            self.stdout.write('\n')
            for var_name, value, docstring \
                in[('Name', 'Value', 'Documentation'),
                   ('---------------', '----------', '-------------')]:
                self.stdout.write(
                    '{0:15}  {1:10}  {2}\n'.format(
                        var_name, value, docstring
                        )
                    )
            for var_name in var_names:
                docstring = getattr(self, f'set_{var_name}').__doc__
                self.stdout.write(
                    '{0:15}  {1:10}  {2}\n'.format(
                        var_name,
                        getattr(self, var_name),
                        docstring if docstring else '<no documentation>',
                    )
                )
        self.stdout.write('\n')

    def do_exit(self, *args_):
        """Exit the prompt."""
        return 1

    def do_set(self, args):
        """Set the value of a variable: set VARIABLE VALUE."""
        try:
            var_name, new_value, *rest = args.split()
        except ValueError:
            self.badinput("try 'set VARIABLE VALUE'")
            return
        else:
            if len(rest) > 0:
                self.default('set ' + args)
                return

        if var_name not in dir(self):
            self.badinput(f"'{var_name}' not defined")
            return

        try:
            func = getattr(self, 'set_' + var_name)
        except AttributeError:
            self.badinput(f"'set_{var_name}' method not found")
            return
        else:
            func(new_value)

    def parsearg(self, arg, parser, raise_error=False):
        """"Parse an argument using a parser.

        Returns the value parsed, in case of success, or None
        otherwise.

        Parameters:
        arg : string
            An argument string to parsed into a value.
        parser :
            A function for parsing.  It should raise a `ValueError` if
            `arg` cannot be parsed.
        raise_error : bool, optional
            A flag for controlling the error handling.  If True, raise
            the exception from parsers.  If False, print the message
            of the parser's exception and return None.

        """
        try:
            value = parser(arg)
        except ValueError as err:
            if raise_error:
                raise err
            else:
                self.stdout.write(f'*** Error: {err.args[0]}\n')
                return
        else:
            return value

    def do_eval(self, arg):
        """Evaluate expression: eval expr"""
        try:
            val = eval(arg)
        except:
            exc_info = sys.exc_info()[:2]
            self.stdout.write(traceback.format_exception_only(*exc_info)[-1].strip())
            self.stdout.write('\n')
        else:
            self.stdout.write(repr(val) + '\n')


class LaserExperiment(InteractiveExperiment, SingleDevice):
    prompt = '(Laser Experiment) '
    mirror_x_chan = None
    mirror_y_chan = None
    excit_chan = None
    read_chan = None
    data_out = None

    def __init__(
            self,
            device_name,
            mirror_x_chan=None,
            mirror_y_chan=None,
            excit_chan=None,
            read_chan=None,
            min_out_volt=-10,
            max_out_volt=+10,
            sampl_rate=1e3,
            distance=100,
            volt_deg_scale=0.24,
    ):
        InteractiveExperiment.__init__(self)
        SingleDevice.__init__(self, device_name)
        self._min_max = tuple(val for val in (min_out_volt, max_out_volt))
        for i, mirror_chan in enumerate(
                [mirror_x_chan, mirror_y_chan, excit_chan, read_chan]):
            if mirror_chan is not None:
                ch = self.add_ao_voltage_chan(
                    mirror_chan,
                    min_val=self._min_max[0],
                    max_val=self._min_max[1]
                )
                if i == 0:
                    self.mirror_x_chan = ch
                elif i == 1:
                    self.mirror_y_chan = ch
                elif i == 2:
                    self.excit_chan = ch
                else:
                    self.read_chan = ch

        self.distance = float(distance)
        self.sampl_rate = float(sampl_rate)
        self.volt_deg_scale = float(volt_deg_scale)
        self.x_pos = 0.0
        self.y_pos = 0.0

    def setup(self):
        """Set sampling rate and samples per channel.

        If `LaserExperiment.data_out` is None, the number of samples
        per channel will 2.

        """
        self.stop()
        self.cfg_samp_clk_timing(
            self.sampl_rate,
            sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
            samps_per_chan= self.data_out.size if self.data_out else 2,
        )

    def set_sampl_rate(self, value):
        """the sampling rate (Hz)"""
        value = self.parsearg(value, float)
        if value is None:
            return
        else:
            self.sampl_rate = value
            self.setup()

    def set_distance(self, value):
        """the distance of the surface (cm)"""
        value = self.parsearg(value, float)
        if not value:
            return
        else:
            self.distance = value

    def set_volt_deg_scale(self, value):
        """the scaling factor (V/deg)"""
        value = self.parsearg(value, float)
        if not value:
            return
        else:
            self.volt_deg_scale = value

    def pos_to_volt_array(self, x_pos, y_pos):
        """Convert from a desired position to output voltage."""
        return tuple(self.volt_deg_scale * 180 / np.pi * \
                     np.arctan2([-x_pos, +y_pos], self.distance))

    def do_point(self, args):
        """Move laiser point to position (x, y): point [X [Y]]"""
        coords = args.split()
        for i in range(0, len(coords)):
            if i == 0:
                self.set_x_pos(coords[i])
            elif i == 1:
                self.set_y_pos(coords[i])
            else:
                self.badinput("try 'point [X [Y]]'")
                return

        x_volt, y_volt = self.pos_to_volt_array(self.x_pos, self.y_pos)
        if self.mirror_x_chan and self.mirror_y_chan:
            data = [[x_volt, x_volt], [y_volt, y_volt]]
        elif self.mirror_x_chan:
            data = [x_volt, x_volt]
        elif self.mirror_y_chan:
            data = [y_volt, y_volt]
        else:
            return

        self.write_task.stop()
        try:
            self.write_task.write(data, auto_start=True)
        except nidaqmx.errors.DaqWriteError as err:
            self.stdout.write(f'*** Error: {err.args[0]}\n\n')

    def set_x_pos(self, value):
        """x position of the laser point (cm)"""
        value = self.parsearg(value, float)
        if value is None:
            return
        else:
            self.x_pos = value

    def set_y_pos(self, value):
        """y position of the laser point (cm)"""
        value = self.parsearg(value, float)
        if value is None:
            return
        else:
            self.y_pos = value

    def do_system(self, *args_):
        """Show information about the system."""
        self.stdout.write('\nDevice:\n')
        if self.ruler:
            self.stdout.write(f'{self.ruler * 7}\n')
        self.stdout.write(f'Name:\t{self.device.name}\n')
        self.stdout.write(f'Type:\t{self.device.product_type}\n\n')
        self.stdout.write('Channels:\n')
        if self.ruler:
                self.stdout.write(f'{self.ruler * 9}\n')
        pairs = [('Mirror (X)', self.mirror_x_chan),
                 ('Mirror (Y)', self.mirror_y_chan),
                 ('Excitation', self.excit_chan),
                 ('Reading', self.read_chan)]
        for name, ch in pairs:
            self.stdout.write('{0}:\t{1}\n'.format(name, repr(ch)))

    def do_start(self, *args_):
        """Start the experiment."""
        self.start()

    def do_stop(self, *args_):
        """Stop the experiment."""
        self.stop()

    def prepare_write_data(self, default_value=0, **channel_data_pairs):
        """Prepare data to be sent to device.

        Prepares a numpy.ndarray with proper shape to be sent to the
        device.  If no channel is defined in current object, returns
        nothing.  If no `channel_data_pairs` is provided, returns
        nothing.

        Parameters:
        default_value : float, optional
            The value to be used in case the channel is not to receive data.
        channel_data_pairs : dict or key=value pairs, optional
            Pairs of the form `<channel_name>=<list of values>` or a
            `dict` whose keys are `<channel name>` and values are
            `<list of values>`.  The keys should be attributes of the
            current object, an not any key.  The list of values should
            all have the same length.

        """
        if channel_data_pairs == {}:
            return
        task_chans = list(self.ao_channels)
        if task_chans == []:
            return
        chosen_chans = {}
        for ch in channel_data_pairs.keys():
            try:
                val = getattr(self, ch)
            except AttributeError:
                raise AttributeError(f"channel '{ch}' is not defined")
            else:
                if val not in task_chans:
                    raise ValueError(f"channel '{ch}' is not valid")
                else:
                    chosen_chans[ch] = val
        try:
            lengths = [len(val) for val in channel_data_pairs.values()]
        except TypeError as err:
            raise TypeError('the data inputs should be lists of values')
        if True in (l != lengths[0] for l in lengths):
            raise ValueError('all data input should have the same length')
        data_out = np.ones((len(task_chans), lengths[0])) * default_value
        for name, ch in chosen_chans.items():
            i = task_chans.index(ch)
            data_out[i, :] = channel_data_pairs[name]
        # Guarantee at least two samples per channel
        nrows, ncols = data_out.shape
        if ncols < 2:
            data_out = np.hstack((data_out, data_out))
        return data_out
