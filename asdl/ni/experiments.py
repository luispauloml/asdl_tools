import cmd
import numpy as np
from . import SingleDevice


class InteractiveExperiment(cmd.Cmd, SingleDevice):
    """Interactive prompts for a task with single device."""
    intro = "Try '?' or 'help' for help."
    prompt = '(Interactive Experiment) '

    def __init__(self, device_name):
        cmd.Cmd.__init__(self)
        SingleDevice.__init__(self, device_name)

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

    def do_system(self, *args_):
        """Show information about the system."""
        self.stdout.write('\nDevice:\n')
        if self.ruler:
            self.stdout.write(f'{self.ruler * 7}\n')
        self.stdout.write(f'Name:\t{self.device.name}\n')
        self.stdout.write(f'Type:\t{self.device.product_type}\n\n')

        channels = \
            [str(ch) for ch in list(self.ai_channels) + list(self.ao_channels)]
        if channels:
            self.print_topics('Channels:', channels, None, 80)
        else:
            self.stdout.write('Channels:\n')
            if self.ruler:
                self.stdout.write(f'{self.ruler * 9}\n')
            self.stdout.write('*** No channels\n\n')

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

    def do_start(self, *args_):
        """Start the experiment."""
        self.start()

    def do_stop(self, *args_):
        """Stop the experiment."""
        self.stop()


class LaserExperiment(InteractiveExperiment):
    prompt = '(Laser Experiment) '
    mirror_x_chan = None
    mirror_y_chan = None
    excit_chan = None
    read_chan = None

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
            volt_deg_scale=0.4,
    ):
        InteractiveExperiment.__init__(self, device_name)
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

        self.distance = distance
        self.sampl_rate = sampl_rate
        self.volt_deg_scale = volt_deg_scale
        self.x_pos = 0
        self.y_pos = 0

    def set_sampl_rate(self, value):
        """the sampling rate (Hz)"""
        try:
            value = float(value)
        except ValueError as err:
            self.stdout.write(f'*** Error: {err.args[0]}')
            return
        self.sampl_rate = value
        self.stdout.write('*** Warning: changing the sampling rate will \
not affect current experiment\n')

    def set_distance(self, value):
        """the distance of the surface (cm)"""
        try:
            value = float(value)
        except ValueError as err:
            self.stdout.write(f'*** Error: {err.args[0]}')
            return
        else:
            self.distance = value

    def set_volt_deg_scale(self, value):
        """the scaling factor (V/deg)"""
        try:
            value = float(value)
        except ValueError as err:
            self.stdout.write(f'*** Error: {err.args[0]}')
            return
        self.volt_deg_scale = value

    def pos_to_volt_array(self, x_pos, y_pos):
        """Convert from a desired position to output voltage."""
        return tuple(self.volt_deg_scale * 180 / np.pi * \
                     np.arctan2([-x_pos, -y_pos], self.distance))

    def do_point(self, args):
        """Move laiser point to position (x, y): point X Y"""
        try:
            x_pos, y_pos, *rest = args.split()
        except ValueError:
            self.badinput("try 'point X Y'")
            return
        else:
            if len(rest) > 0:
                self.default('point ' + args)
                return

        vals = []
        for val in [x_pos, y_pos]:
            try:
                val = float(val)
            except ValueError:
                self.badinput('the arguments should be numbers')
                return
            else:
                vals.append(val)

        x_volt, y_volt = self.pos_to_volt_array(*vals)
        if self.mirror_x_chan and self.mirror_y_chan:
            data = [[x_volt, x_volt], [y_volt, y_volt]]
        elif self.mirror_x_chan:
            data = [x_volt, x_volt]
        elif self.mirror_y_chan:
            data = [y_volt, y_volt]
        else:
            self.x_pos, self.y_pos = vals
            return

        self.write_task.stop()
        try:
            self.write_task.write(data, auto_start=True)
        except ni.errors.DaqWriteError as err:
            self.stdout.write(f'*** Error: {err.args[0]}\n\n')
            self.write_task.start()
        else:
            self.x_pos, self.y_pos = vals

    def set_x_pos(self, new_value):
        """x position of the laser point (cm)"""
        self.do_point(f'{new_value} {self.y_pos}')

    def set_y_pos(self, new_value):
        """y position of the laser point (cm)"""
        self.do_point(f'{self.x_pos} {new_value}')
