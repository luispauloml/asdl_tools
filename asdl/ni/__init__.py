"""A module to handle NI-DAQmx write and read tasks."""

import builtins
import nidaqmx
import warnings
import functools


__all__ = ['Task', 'SingleDevice', 'available_devices']


def available_devices():
    """List of NI-DAQ devices connected to current machine.

    Returns a list of `nidaqmx.system.device.Device` objects
    representing each device currently connected and detected by
    NI-DAQmx drivers.

    """
    system = nidaqmx.system.System.local()
    return list(system.devices)


def _catch_excpetions(funcs, except_type, except_codes=None,
                      qtde=1, args=(), kwargs={}):
    """Catch errors or warnings coming from DAQmx.

    Catches errors of type `exception_type`, for `qtde` times or raise
    it otherwise.  If `qtde + 1` errors are caught, the last one will
    be risen.  If `error_code` is given and the error's code is not
    equal to it, the error will be risen.

    Parameters:
    funcs : list
        A list of functions to be called.
    except_type : type
        The type of exception to be caught.  Should be a subclasse of
        builtin.Exception or builtins.Warning.
    qtde :  int, default=1
        Number of erros to be caught before an exception is raised.
    except_codes : int or list, defualt=None
        The error codes.  If None, there will be no error code
        comparison.
    args : tupe, default=()
        A tuple with positional arguments to be passed to the
        functions in `funcs`.
    kwargs : dict, default={}
        A dictionary with the keywork arguments to be passed to the
        functions in `funcs`.

    """
    count = 0
    if isinstance(except_codes, int):
        except_codes = [except_codes]

    if issubclass(except_type, builtins.Warning):
        with warnings.catch_warnings(record=True) as caught_warnings:
            for func in funcs:
                func()
        for warning in caught_warnings:
            if issubclass(warning.category, except_type):
                count += 1
                if count > qtde:
                    warnings.warn(warning.message, warning.category)
                    break
            else:
                warnings.warn(warning.message, warning.category)

    elif issubclass(except_type, builtins.Exception):
        for i, func in enumerate(funcs):
            try:
                func(*args, **kwargs)
            except except_type as e:
                if except_codes is None:
                    count += 1
                else:
                    if e.error_code in except_codes:
                        count += 1
                    else:
                        raise e
                if count > qtde:
                    raise e
                else:
                    pass

    else:
        raise TypeError(f'{except_type} is neither an Exception nor a Warning')


def _dispatch(target_func, func_name=None):
    """Decorator to copy docstrings and attach a message to it.

    Parameters:
    target_func : function or method
        Target function from which the docstring will be copied.
    func_name : str or None, optional
        The name of function written in the note at the end of the
        docstring.  If None, no message is attached.

    """
    def decorator(func):
        @functools.wraps(target_func)
        def worker(*args, **kwargs):
            return func(*args, **kwargs)

        # Add message to __doc__
        if func_name is not None:
            worker.__doc__ += f"""

        Note: this method dispatches to `{func_name}`.
        """

        return worker
    return decorator


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

    NOTE: unless otherwise stated, every method is first executed on
    the write task frist, and on the read task second.

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

    @_dispatch(nidaqmx.Task.close, 'nidaqmx.Task.close')
    def close(self):
        _catch_excpetions([self.write_task.close, self.read_task.close],
                          nidaqmx.DaqResourceWarning,
                          qtde=2)

    @_dispatch(nidaqmx.Task.start, 'nidaqmx.Task.start')
    def start(self):
        # The order of calling is relevant because, should reading and
        # writing tasks be synchronized, the write task will be
        # configure to wait for a trigger from the read task,
        # therefore it has to start first and wait for the read task
        # to be started.
        _catch_excpetions([self.write_task.start, self.read_task.start],
                        nidaqmx.DaqError,
                        nidaqmx.error_codes.DAQmxErrors.INVALID_TASK)

    @_dispatch(nidaqmx.Task.stop, 'nidaqmx.Task.stop')
    def stop(self):
        _catch_excpetions([self.write_task.stop, self.read_task.stop],
                        nidaqmx.DaqError,
                        nidaqmx.error_codes.DAQmxErrors.INVALID_TASK)

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

        try:
            self.read_task.timing.samp_clk_rate = \
                self.write_task.timing.samp_clk_rate
            self.write_task.triggers.start_trigger.cfg_dig_edge_start_trig(
                self.read_task.triggers.start_trigger.term
            )
            self.write_task.start()
        except nidaqmx.DaqError as err:
            if err.error_code not in \
               [nidaqmx.error_codes.DAQmxErrors.\
                CAN_NOT_PERFORM_OP_WHEN_NO_DEV_IN_TASK,
                nidaqmx.error_codes.DAQmxErrors.INVALID_TASK]:
                raise err

    @_dispatch(nidaqmx.Task.is_task_done, 'nidaqmx.Task.is_task_done')
    def is_task_done(self):
        try:
            write_is_done = self.write_task.is_task_done()
        except nidaqmx.DaqError as err:
            if err.error_code == nidaqmx.error_codes.DAQmxErrors.INVALID_TASK:
                write_is_done = True
            else:
                raise err
        try:
            read_is_done = self.read_task.is_task_done()
        except nidaqmx.DaqError as err:
            if err.error_code == nidaqmx.error_codes.DAQmxErrors.INVALID_TASK:
                read_is_done = True
            else:
                raise err

        return write_is_done and read_is_done

class SingleDevice(Task):
    """Manage tasks for a single NI device.

    This class makes `Task` more specific by working with a single
    device.  Most of its methods are dispatched verbatim to their
    corresponding counterparts in `nidaqmx.Task`.  Because of that,
    the documentation for many methods are also the same as those in
    `nidaqmx`.

    Parameters:
    device_name : str
        The name of the device assigned to it by the NI-DAQmx driver.

    """
    def __init__(self, device_name):
        devices = [device
                   for device in nidaqmx.system.System.local().devices
                   if device.name == device_name]
        if devices == []:
            raise ValueError(f"device not found: '{device_name}'")
        elif len(devices) > 1:
            raise SystemError(f"there is more then one device '{device_name}")
        else:
            self._device = devices[0]
        Task.__init__(self)

    def __del__(self):
        try:
            Task.__del__(self)
        except AttributeError:
            # The attributes `read_task` and `write_task` do not
            # exist and there is nothing to be deleted.
            pass

    @property
    def device(self):
        """The device using in the tasks."""
        return self._device

    @property
    @_dispatch(nidaqmx.Task.ai_channels)
    def ai_channels(self):
        return self.read_task.ai_channels

    @property
    @_dispatch(nidaqmx.Task.ao_channels)
    def ao_channels(self):
        return self.write_task.ao_channels

    @_dispatch(nidaqmx._task_modules.ai_channel_collection.\
               AIChannelCollection.add_ai_voltage_chan,
               'nidaqmx._task_modules.ai_channel_collection.\
               AIChannelCollection.add_ai_voltage_chan')
    def add_ai_voltage_chan(self, physical_channel, *args, **kwargs):
        # Try to take `physical_channel`  as an int
        try:
            ch = self.ai_channels.add_ai_voltage_chan(
                f'{self.device.name}/ai{physical_channel}',
                *args, **kwargs)

        # If it fails, check the code error and try the actual value
        # of `physical_channel`
        except nidaqmx.DaqError as err:
            codes = \
                [nidaqmx.error_codes.DAQmxErrors.PHYSICAL_CHAN_DOES_NOT_EXIST,
                 nidaqmx.error_codes.DAQmxErrors.PHYSICAL_CHANNEL_NOT_SPECIFIED]

            if err.error_code in codes:
                ch = self.ai_channels.add_ai_voltage_chan(
                    physical_channel, *args, **kwargs)
                return ch
            else:
                raise err

        else:
            return ch

    @_dispatch(nidaqmx._task_modules.ao_channel_collection.\
               AOChannelCollection.add_ao_voltage_chan,
               'nidaqmx._task_modules.ao_channel_collection.\
               AOChannelCollection.add_ao_voltage_chan')
    def add_ao_voltage_chan(self, physical_channel, *args, **kwargs):
        # Try to take `physical_channel`  as an int
        try:
            ch = self.ao_channels.add_ao_voltage_chan(
                f'{self.device.name}/ao{physical_channel}',
                *args, **kwargs)

        # If it fails, check the code error and try the actual value
        # of `physical_channel`
        except nidaqmx.DaqError as err:
            codes = \
                [nidaqmx.error_codes.DAQmxErrors.PHYSICAL_CHAN_DOES_NOT_EXIST,
                 nidaqmx.error_codes.DAQmxErrors.PHYSICAL_CHANNEL_NOT_SPECIFIED]

            if err.error_code in codes:
                ch = self.ao_channels.add_ao_voltage_chan(
                    physical_channel, *args, **kwargs)
                return ch
            else:
                raise err

        else:
            return ch

    @_dispatch(nidaqmx.Task.write, 'nidaqmx.Task.write')
    def write(self, *args, **kwargs):
        return self.write_task.write(*args, **kwargs)

    @_dispatch(nidaqmx.Task.read, 'nidaqmx.Task.read')
    def read(self, *args, **kwargs):
        return self.read_task.read(*args, **kwargs)

    @_dispatch(nidaqmx._task_modules.timing.Timing.cfg_samp_clk_timing,
               'nidaqmx._task_modules.timing.Timing.cfg_samp_clk_timing')
    def cfg_samp_clk_timing(self, *args, **kwargs):
        _catch_excpetions(
            [self.write_task.timing.cfg_samp_clk_timing,
             self.read_task.timing.cfg_samp_clk_timing],
            nidaqmx.DaqError,
            [nidaqmx.error_codes.DAQmxErrors.INVALID_TASK,
             nidaqmx.error_codes.DAQmxErrors.CAN_NOT_PERFORM_OP_WHEN_NO_DEV_IN_TASK],
            args=args, kwargs=kwargs,
        )
