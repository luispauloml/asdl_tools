import numbers
import numpy as np
from collections.abc import Iterable

class MeasuredData(object):
    """Objects to stored measured or computed values"""

    def __init__(self):
        self._data = {'space': None, 'time': None, 'results': None}
        self._steps = {'time': None, 'space': None}

    def _set_steps(self, step, value):
        if isinstance(value, numbers.Number) or value is None:
            if step in ['time', 'freq']:
                if value is None:
                    self._steps['time'] = None
                else:
                    # Sampling frequency and time step should
                    # be set together
                    if step == 'freq':
                        self._steps['time'] = (value, 1/value)
                    else:
                        self._steps['time'] = (1/value, value)
            elif step == 'space':
                self._steps['space'] = value
            else:
                raise ValueError('invald step')
        else:
            raise TypeError('the value should be a number or None')

    @property
    def fs(self):
        """the sampling frequency"""
        return self._steps['time'][0]

    @fs.setter
    def fs(self, value):
        self._set_steps('freq', value)

    @property
    def dt(self):
        """the time step"""
        return self._steps['time'][1]

    @dt.setter
    def dt(self, value):
        self._set_steps('time', value)

    @property
    def dx(self):
        """the step in space"""
        return self._steps['space']

    @dx.setter
    def dx(self, value):
        self._set_steps('space', value)

    @property
    def data(self):
        """the data contained in this object"""
        return self._data['results']

    def purge_data(self):
        """Delete the data stored in the object."""
        self._data = MeasuredData()._data

    @property
    def time_vect(self):
        """a vector with the time discretized"""
        return self._data['time']

    @time_vect.setter
    def time_vect(self, vect):
        self._data['time'] = vect

    @property
    def x_vect(self):
        """a vector of the discretization of space in the x direction"""
        raise NotImplementedError

    @property
    def y_vect(self):
        """a vector of the discretization of space in the y direction"""
        raise NotImplementedError

class BaseWave(MeasuredData):
    """Base class to define Wavepacket and Surface"""

    def _set_tuple_value(self, field, value,
                         predicate, err, apply_to_values):
        dict_ = self.__dict__

        if value is None:
            dict_[field] = None
            return

        if not isinstance(value, tuple):
            self._set_tuple_value(field, (0, value), predicate,
                                  err, apply_to_values)
        else:
            new_values = []
            # Use range to guarantee that only two values will be accounted for
            for i in range(0, 2):
                if not predicate(value[i]):
                    raise err
                else:
                    new_values.append(apply_to_values(value[i]))

            dict_[field] = (new_values[0], new_values[1])

    @property
    def space_boundary(self):
        raise NotImplementedError

    @space_boundary.setter
    def space_boundary(self, L):
        raise NotImplementedError

    @property
    def time_boundary(self):
        """the limits of the time domain"""
        return self._tlim

    @time_boundary.setter
    def time_boundary(self, T):
        pred = lambda x: isinstance(x, numbers.Number)
        err = TypeError('The limits of for the time should be numbers.')
        self._set_tuple_value('_tlim', T, pred, err, lambda x: x)

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

    def _get_time_or_space(self, flag):
        if flag == 'time':
            step, lims = self.dt, '_tlim'
            field, err = 'time', 'Either `fs` or `time` are not set.'
        elif flag == 'space':
            step, lims = self.dx, '_xlim'
            field, err = 'space', 'Either `dx` or `domain` are not set.'
        else:
            raise ValueError('something went wrong')

        if step is None or self.__dict__[lims] is None:
            raise ValueError(err)

        # Return stored values
        v1, v2 = self.__dict__[lims]
        values = self._data[field]

        # Check with current properties
        if values is not None:
            if (step == values[1] - values[0] and
                values[0] == v1 and
                values[-1] == v2):
                return self._data[field]

        # If check fails, re-evaluate
        # Due to floating point errors, to avoid changes in size of
        # the output, I add a quarter of the step to the upper limit
        self._data[field] = np.arange(v1, v2 + step / 4, step)
        self.__dict__[lims] = (self._data[field][0], self._data[field][-1])
        return self._data[field]

    @property
    def time_vect(self):
        """a vector with the time discretized"""
        return self._get_time_or_space('time')
