from collections.abc import Iterable
import numbers
import numpy as np

class BaseWave:
    """Base class to define Wavepacket and Membrane"""

    def __init__(self):
        self._data = {'domain': None, 'time': None, 'results': None}

    def _set_scalar(self, field, value, apply_to_value, if_none, err):
        dict_ = self.__dict__
        if value is None:
            if_none()
        elif isinstance(value, numbers.Number):
            dict_[field] = apply_to_value(value)
        else:
            raise TypeError(err)

    @property
    def fs(self):
        """the sampling frequency"""
        if self.dt is None:
            return None
        else:
            return 1/self.dt

    @fs.setter
    def fs(self, value):
        err = 'the sampling frequency should be a number.'
        def if_none(obj):
            def worker():
                obj.dt = None
            return worker
        self._set_scalar('dt', value, lambda x: 1/x, if_none(self), err)

    @property
    def dx(self):
        """the step in space"""
        return self._step

    @dx.setter
    def dx(self, value):
        err = 'the step in space should be a number.'
        def if_none(obj):
            def worker():
                obj._step = None
            return worker
        self._set_scalar('_step', value, lambda x: x, if_none(self), err)

    def _set_tuple_value(self, field, discretized_field, value, err):
        dict_ = self.__dict__
        dict_[discretized_field] = None

        if value is None:
            dict_[field] = None
            return

        if not isinstance(value, tuple):
            self._set_tuple_value(field, discretized_field, (0, value), err)
        else:
            for i in range(0, 2):
                if not isinstance(value[i], numbers.Number):
                    raise ValueError(err)
            dict_[field] = (value[0], value[1])

    @property
    def domain(self):
        """the limits of the space domain"""
        return self._xlim

    @domain.setter
    def domain(self, L):
        err = 'The limits of the domain should be numbers.'
        self._set_tuple_value('_xlim', '_xs', L, err)

    @property
    def time(self):
        """the limits of the time domain"""
        return self._tlim

    @time.setter
    def time(self, T):
        err = 'The limits of for the time should be numbers.'
        self._set_tuple_value('_tlim', '_ts', T, err)

    @property
    def normalize(self):
        """flag for noramlization of values"""
        return self._normalize_flag

    @normalize.setter
    def normalize(self, flag):
        # Use if statement to garantee that `normalize` becomes bool
        if flag:
            self._normalize_flag = True
        else:
            self._normalize_flag = False

    def _set_list_value(self, field, values, predicate, err, if_none):
        dict_ = self.__dict__
        dict_[field] = []
        if isinstance(values, Iterable):
            for v in values:
                if not predicate(v):
                    raise TypeError(err)
                else:
                    dict_[field].append(v)
            return

        elif values is None:
            if_none()

        else:
            self._set_list_value(field, [values], predicate, err, if_none)

    def eval(self):
        raise NotImplementedError

    def purge_data(self):
        """Delete the evaluated data stored in the object."""

        del(self._data)
        self._data = BaseWave()._data

    def _get_time_or_space(self, flag):
        if flag == 'time':
            step, lims = self.dt, self.time
            field, err = 'time', 'Either `fs` or `time` are not set.'
        elif flag == 'space':
            step, lims = self.dx, self.domain
            field, err = 'domain', 'Either `dx` or `domain` are not set.'
        else:
            raise ValueError('something went wrong')

        if step is None or lims is None:
            raise ValueError(err)

        # Return stored values
        v1, v2 = lims
        values = self._data[field]

        # Check with current properties
        if values is not None:
            if (step == values[1] - values[0] and
                values[0] == v1 and
                values[-1] == v2):
                return self._data[field]

        # If check fails, re-evaluate
        self._data[field] = np.arange(v1, v2, step)
        return self._data[field]

    def get_time(self):
        """Return the discretized time domain."""
        return self._get_time_or_space('time')
