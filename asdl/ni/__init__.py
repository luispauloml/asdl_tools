"""A module to handle NI-DAQmx write and read tasks."""

import nidaqmx


class Task:
    """Creates two NI-DAQmx Tasks for writing and reading.

    The purpose of the object is to have one single object that
    carries both independent tasks required by `nidaqmx` for writing
    and reading, the `write_task` and `read_task` attributes
    respectively.

    There are a few convenience methods, but, ultimately, each task
    should be configure independently.  Each attribute is an instance
    of `nidaqmx.Task`, and one should use `dir` to discover their
    methods, and `help` for more information, e.g.

        >>> task = Task()
        >>> dir(task.read_task)
        ...
        >>> help(task.read_task.<method>)
        ...

    For documentation on `nidaqmx`, see:
    <https://nidaqmx-python.readthedocs.io/>

    """

    def __init__(self):
        self.write_task = nidaqmx.Task()
        self.read_task = nidaqmx.Task()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.write_task.__del__()
        self.read_task.__del__()

    def close(self):
        """Clear tasks.

        It calls `close` method first on the write task, and then on
        the read task.

        """
        self.write_task.close()
        self.read_task.close()

    def start(self):
        """Start tasks.

        It calls `start` method first on the write task, and then on
        the read task.

        """
        # The order of calling is relevant because, should reading and
        # writing tasks be synchronized, the write task will be
        # configure to wait for a trigger from the read task,
        # therefore it has to start first and wait for the read task
        # to be started.
        self.write_task.start()
        self.read_task.start()

    def stop(self):
        """Stop tasks.

        It calls `stop` method first on the write task, and then on the
        read task.

        """
        self.write_task.stop()
        self.read_task.stop()

    def synchronize(self):
        """Synchronize read and write tasks.

        It does three things:
        1. sets the read task's sample clock rate to be equal to that
           of the write task,
        2. configures the write task to wait for a digital trigger coming
           from the read task.
        3. starts the write task.

        Because of the last step, is recommended that this method is
        called after configuring the write task.

        """
        # See <https://github.com/ni/nidaqmx-python/issues/162>

        self.read_task.timing.samp_clk_rate = \
            self.write_task.timing.samp_clk_rate

        self.write_task.triggers.start_trigger.cfg_dig_edge_start_trig(
            self.read_task.triggers.start_trigger.term)

        self.write_task.start()

    def cfg_samp_clk_timing(self, *args, **kwargs):
        timing = self.write_task.timing
        timing.cfg_samp_clk_timing(*args, **kwargs)

        timing = self.read_task.timing
        timing.cfg_samp_clk_timing(*args, **kwargs)

    cfg_samp_clk_timing.__doc__ = \
        nidaqmx._task_modules.timing.Timing.cfg_samp_clk_timing.__doc__
    cfg_samp_clk_timing.__doc__ += """
        NOTE: this method simply dispatches from `asdl.ni.Task` to
        `nidaqmx.Task` and runs this method first on the write task, and the
        on the read task."""
