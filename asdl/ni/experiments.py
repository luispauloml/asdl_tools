import cmd
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

    def do_setup(self, _):
        """Run the setup."""
        return self.setup()

    def do_variables(self, _):
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
                        self.__dict__[var_name],
                        docstring if docstring else '<no documentation>',
                    )
                )
        self.stdout.write('\n')

    def do_system(self, _):
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

    def do_exit(self, _):
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

        try:
            old_value = self.__dict__[var_name]
        except KeyError:
            self.badinput(f"'{var_name}' not defined")
            return

        try:
            func = getattr(self, 'set_' + var_name)
        except AttributeError:
            self.badinput(f"'set_{var_name}' method not found")
            return
        else:
            func(self, new_value)

    def do_start(self, _):
        """Start the experiment."""
        self.start()

    def do_stop(self, _):
        """Stop the experiment."""
        self.stop()
