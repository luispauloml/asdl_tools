import cmd
from . import SingleDevice


class InteractiveExperiment(cmd.Cmd, SingleDevice):
    """Interactive prompts for a task with single device."""
    intro = "Try '?' or 'help' for help."
    prompt = '(Interactive Experiment) '

    def __init__(self, device_name):
        cmd.Cmd.__init__(self)
        SingleDevice.__init__(self, device_name)
        self._variables_docstrings = {}

    def emptyline(self):
        """Print nothing."""
        self.stdout.write('')

    def setup(self):
        """Set up the system.

        This method does nothing unless it is overridden.

        """
        pass

    def do_setup(self, _):
        """Run the setup."""
        return self.setup()

    def register_variable(self, var_name, docstring=None):
        """Register a variable to be available for `set` command.

        Parameters:
        var_name : str 
            The name of the variable to be registered.
        docstring : str
            The documentation of the variable to be shown in the
            `variables` command.
        """
        try:
            self.__dict__[var_name]
        except KeyError:
            raise ValueError(f"variable '{var_name}' is not defined")
        else:
            self._variables_docstrings[var_name] = docstring

    def do_variables(self, _):
        """List all variables that can be changed."""
        self.stdout.write('\nVariables:\n')
        if self.ruler:
            self.stdout.write(f'{self.ruler * 10}\n')
        if self._variables_docstrings == {}:
            self.stdout.write('*** No variables defined\n')
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
            for var_name, docstring in self._variables_docstrings.items():
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
            self.stdout.write("*** Bad input: try 'set VARIABLE VALUE'\n")
            return
        else:
            if len(rest) > 0:
                self.default('set ' + args)
                return

        try:
            old_value = self.__dict__[var_name]
        except KeyError:
            self.stdout.write(f"*** Bad input: '{var_name}' not defined\n")
            return

        try:
            new_value = float(new_value)
        except ValueError:
            self.stdout.write('*** Bad input: VALUE should be a number\n')
            return

        self.__dict__[var_name] = new_value

        try:
            func = getattr(self, 'set_' + var_name + '_hook')
        except AttributeError:
            return None
        return func(new_value, old_value)
