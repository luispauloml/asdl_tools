import cmd
import nidaqmx
import numpy as np
import traceback
import time
import sys
from . import SingleDevice, _dispatch
from .. import MeasuredData, DataCollection


__all__ = ['InteractiveExperiment', 'LaserExperiment']


def sort_channels(collection, channels):
    """Find the order of channels in a collection of channels.

    Returns a list with the indexes of the elements of `channels` in
    `collection`.

    Parameters:
    collection :  Iterable
        A collection of channels from a device.
    channels : list
        The channels whose indexes in `collection` will be returned.

    """
    collection = list(collection)
    idx = []
    for ch in collection:
        idx.append(collection.index(ch))
    return idx


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

    def help_variables(self):
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
                   ('---------------', '---------------', '-------------')]:
                self.stdout.write(
                    '{0:15}  {1:15}  {2}\n'.format(
                        var_name, value, docstring
                        )
                    )
            for var_name in var_names:
                docstring = getattr(self, f'set_{var_name}').__doc__
                self.stdout.write(
                    '{0:15}  {1:15}  {2}\n'.format(
                        var_name,
                        repr(getattr(self, var_name)),
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


class LaserExperiment(InteractiveExperiment):
    prompt = '(Laser Experiment) '
    mirror_x_chan = None
    mirror_y_chan = None
    excit_chan = None
    read_chan = None
    data_out = None
    global_variables = ['data_out']
    local_variables = ['y_pos', 'x_pos', 'sampl_rate']

    def __init__(
            self,
            laser_device,
            mirrors_device,
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

        self.laser_task = SingleDevice(laser_device)
        self.mirrors_task = SingleDevice(mirrors_device)
        self._devices = (self.laser_task.device, self.mirrors_task.device)

        self._min_max = (float(min_out_volt), float(max_out_volt))
        self.point_offset = (0, 0)

        if mirror_x_chan is None:
            mirror_x_chan = self.mirror_x_chan
        if mirror_y_chan is None:
            mirror_y_chan = self.mirror_y_chan
        for i, mirror_chan in enumerate([mirror_x_chan, mirror_y_chan]):
            if mirror_chan is not None:
                ch = self.mirrors_task.add_ao_voltage_chan(
                    mirror_chan,
                    min_val=self._min_max[0],
                    max_val=self._min_max[1]
                )
                if i == 0:
                    self.mirror_x_chan = ch
                elif i == 1:
                    self.mirror_y_chan = ch

        read_chan = [ch
                     for ch in [read_chan, self.read_chan]
                     if ch is not None]
        if read_chan != []:
            ch = self.laser_task.add_ai_voltage_chan(
                read_chan[0],
                min_val=self._min_max[0],
                max_val=self._min_max[1],
            )
            self.read_chan = ch

        excit_chan = [ch
                      for ch in [excit_chan, self.excit_chan]
                      if ch is not None]
        if excit_chan != []:
            ch = self.laser_task.add_ao_voltage_chan(
                excit_chan[0],
                min_val=self._min_max[0],
                max_val=self._min_max[1],
            )
            self.excit_chan = ch

        self.samples_per_chan = 2
        self.distance = float(distance)
        self.sampl_rate = float(sampl_rate)
        self.volt_deg_scale = float(volt_deg_scale)
        self.x_pos = 0.0
        self.y_pos = 0.0
        self.data_in = DataCollection()
        self.store_variables('global')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.laser_task.close()
        self.mirrors_task.close()

    def __del__(self):
        self.laser_task.__del__()
        self.mirrors_task.__del__()

    @property
    def laser_device(self):
        """the device used to read from laser and write to vibration source"""
        return self.laser_task.device

    @property
    def mirrors_device(self):
        """the device used to control X and Y mirros"""
        return self.mirrors_task.device

    def store_variables(self, local_or_global, index=-1):
        """Store or update variables to be saved.

        Store variables of current experiment in collection of data so
        that it can be saved.  The list of variables are class
        attributes:
        - `global_variables`, default=['data_out']
        - `local_variables`, default=['x_pos', 'y_pos', 'sampl_rate']

        Parameters:
        local_or_global : {'local' | 'global'}
            Controls whether the variables will be saved as a global
            variable in the collection of experiments, or as local
            variables for one single experiment.
        index : int, optional
            If `local_or_global` is 'local', then `index` indicates
            the index of the experiment in which the variables should
            be stored.  The default is -1, the last added data.

        """
        if local_or_global == 'local':
            attr = 'local_variables'
        elif local_or_global == 'global':
            attr = 'global_variables'
        else:
            raise ValueError(
                f"expected 'local_or_global' or global one of \
{'local' | 'global'}, got '{str(local_or_global)}'"
            )
        try:
            var_names = getattr(self, attr)
        except AttributeError:
            raise AttributeError(f"'{attr}' not found")
        if not isinstance(self.global_variables, list):
            raise TypeError(
                "expected '{0}' as a list, got {1}".format(
                    attr,
                    type(self.global_variables)
                )
            )
        data = {}
        for var_name in var_names:
            if not isinstance(var_name, str):
                raise TypeError(
                    f'expected variable name as str, got {type(var_name)}'
                    )
            try:
                data[var_name] = getattr(self, var_name)
            except AttributeError:
                raise AttributeError(f"variable '{var_name}' is not \
defined in current experiment")
        if local_or_global == 'global':
            self.data_in.__dict__.update(data)
        else:
            self.data_in[index].__dict__.update(data)

    def setup(self, write=False):
        """Set sampling rate and samples per channel for laser task.

        If `LaserExperiment.data_out` is None or `write` is False, the
        number of samples per channel will set to 2.

        Parameters:
        write : bool, optional
            Control the writing task.  If True, prepare samples for
            all channels, keeping the laser point in a fixed position,
            and synchronize reading and writing.  Default is False.
        """
        if not write:
            nsamps = 2
        else:
            if self.data_out is None or len(self.data_out) == 0:
                raise ValueError("cannot write: 'data_out' is empty")
            else:
                nsamps = self.data_out.shape
                if len(nsamps) != 1:
                    raise ValueError("cannot write: 'data_out' should be 1D array")
                nsamps, = nsamps
        self.samples_per_chan = nsamps
        self.laser_task.stop()
        self.laser_task.cfg_samp_clk_timing(
            self.sampl_rate,
            sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
            samps_per_chan=nsamps,
        )
        if write:
            self.laser_task.write(list(self.data_out), auto_start=False)
            self.laser_task.synchronize()

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
        self.point()

    def point(self, x=None, y=None):
        """Move laser point to position (x, y).

        Parameters:
        x : float, optional
           The x-coordinate. If None (the default), uses current value
           of `x_pos` attribute.
        y : float
           The y-coordnate.  If None (the default), uses current value
           of `y_pos` attribute.

        """
        self.x_pos = self.x_pos if x is None else float(x)
        self.y_pos = self.y_pos if y is None else float(y)
        if self.mirror_x_chan is None and self.mirror_y_chan is None:
            return
        volts = self.pos_to_volt_array(self.x_pos + self.point_offset[0],
                                       self.y_pos + self.point_offset[1])
        idx = sort_channels(
            self.mirrors_task.ao_channels,
            [ch for ch in [self.mirror_x_chan, self.mirror_y_chan]
             if ch is not None]
        )
        data = list(range(0, len(idx)))
        for i in idx:
            data[i] = volts[i]
        self.mirrors_task.write_task.stop()
        try:
            self.mirrors_task.write_task.write(data, auto_start=True)
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

    def help_system(self):
        """Show information about the system."""
        self.stdout.write('\nDevices:\n')
        if self.ruler:
            self.stdout.write(f'{self.ruler * 8}\n')
        self.stdout.write(f"""Device\t\tName\t\tType
------\t\t----\t\t----
Laser\t\t{self.laser_device.name}\t\t{self.laser_device.product_type}
Mirrors\t\t{self.mirrors_device.name}\t\t{self.mirrors_device.product_type}
\n""")
        self.stdout.write('Channels:\n')
        if self.ruler:
                self.stdout.write(f'{self.ruler * 9}\n')
        pairs = [('Mirror (X)', self.mirror_x_chan),
                 ('Mirror (Y)', self.mirror_y_chan),
                 ('Excitation', self.excit_chan),
                 ('Reading', self.read_chan)]
        for name, ch in pairs:
            self.stdout.write('{0}:\t{1}\n'.format(name, repr(ch)))

    def do_setup(self, args):
        """Run setup procedure: setup [write]
        If `write` is passed, prepare for writing to the device."""
        try:
            write_flag, *rest = args.split()
        except ValueError:
            write_flag = None
        else:
            if len(rest) > 0:
                self.badinput("wrong number of arguments")
                return
        if write_flag is not None and write_flag != 'write':
            self.badinput("try 'setup [write]'")
            return
        write_flag = write_flag == 'write'
        self.setup(write=write_flag)

    def read(self, nsamples='all', store=True):
        """Read data from the read task.

        This method has several steps:
        1. run the setup with 'write' option,
        2. read data from the read task,
        3. run `postprocess` on the data,
        4. optionally store it,
        5. run `read_hook`,
        6. return the post-processed data.

        Parameters:
        nsamples : {'all' | int}, optional
            The number of samples to be read.  If 'all' read the same
            number of samples there are in `data_out`.  If an int is
            given, read only that number of samples, which is still
            has the length of `data_out` as the upper bound.  Default
            is 'all'.
        store : bool, optional
            If True, store the read data and local variables.  If
            False, do not store anything.  Default is True.

        """
        self.setup(write=True)
        if nsamples == 'all':
            nsamples = self.samples_per_chan
        else:
            nsamples = int(nsamples)
        data = self.laser_task.read_task.read(nsamples)
        data = self.postprocess(data)
        if store:
            self.data_in.append(MeasuredData())
            self.store_variables('local')
            self.data_in.last.data_read = data
        self.read_hook()
        return data

    def do_read(self, _):
        """Read data and store it"""
        self.read(nsamples='all', store=True)

    def postprocess(self, data):
        """Post-process the data.

        Function to be applied to the raw data returned by the device.
        If not overridden, this is the identity function, i.e.
        f(x) = x.

        Parameters:
        data : list
            The list floats returned by NI-DAQmx.

        """
        return data

    def read_hook(self):
        """Hook to be run after reading and post-processing data.

        It should not receive any argument.  If not overridden, it
        does nothing.

        """
        pass

    @_dispatch(DataCollection.save, 'DataCollection.save')
    def save(self, *args, **kwargs):
        self.data_in.save(*args, **kwargs)

    def move(self, x=0, y=0):
        """Move laser point by an amount of (x, y).

        Parameters:
        x : float, optional
            The amount to move the laser point in the X direction.
            Default is 0.
        y : float, optional
            The amount to move the laser point in the Y direction.
            Defualt is 0.

        """
        self.x_pos += float(x)
        self.y_pos += float(y)
        self.point()

    def do_move(self, args):
        """Move point: move {X | Y}  DELTA
        Move point in direction X or Y by DELTA cm."""
        try:
            direction, delta, *rest = args.split()
        except ValueError:
            self.badinput(args)
            return
        else:
            if len(rest) > 0:
                self.badinput(args)
                return
        direction = direction.upper()
        if direction.upper() not in ['X', 'Y']:
            self.badinput("direction should be either 'X' or 'Y'")
            return
        try:
            delta = float(delta)
        except ValueError as err:
            self.badinput(err.args[0])
            return
        if direction == 'X':
            self.move(x=delta)
        else:
            self.move(y=delta)

    def offset(self, x=None, y=None):
        """Set offset for point position and set position to (0, 0).

        The offset is such that the actual (x', y') position of the
        laser point is:
            x' = x + x_pos
            y' = y + y_pos

        Parameters:
        x : float, optional
            The offset in the X direction (cm).  If None, use current
            position.
    y : float, optional
            The offset in the Y direction (cm).  If None, use current
            position.

        """
        if x is None:
            x = self.x_pos + self.point_offset[0]
            new_x_pos = 0
        else:
            new_x_pos = self.x_pos
        if y is None:
            y = self.y_pos + self.point_offset[1]
            new_y_pos = 0
        else:
            new_y_pos = self.y_pos
        self.point_offset = (x, y)
        self.x_pos, self.y_pos = new_x_pos, new_y_pos

    def do_offset(self, _):
        """Set current position (x, y) as offset."""
        self.offset()

    def set_point_offset(self, new_value):
        """X and Y offset (cm, cm)"""
        try:
            x, y, *rest = eval(new_value)
        except TypeError:
            self.badinput(new_value)
            return
        except ValueError:
            self.badinput(new_value)
            return
        else:
            if len(rest) > 0:
                self.badinput(new_value)
        try:
            x, y = float(x), float(y)
        except ValueError as err:
            self.badinput(err.args[0])
            return
        self.point_offset = (x, y)

    def do_save(self, file_name):
        """Save data from experiment to a file: save FILENAME
        Note: this command overwrites existing files."""
        self.data_in.timestamp = \
            f"{time.strftime('%a, %d %b %Y %H:%M:%S %z', time.localtime())}"
        self.save(file_name, overwrite=True)

    @_dispatch(SingleDevice.close)
    def close(self):
        self.laser_task.close()
        self.mirrors_task.close()

    def purge(self):
        """Delete data stored in current experiment.

        Delete all previous read data and re-store global variables.

        """
        self.data_in = DataCollection()
        self.store_variables('global')

    def do_purge(self, _):
        """Delete stored data."""
        self.purge()
