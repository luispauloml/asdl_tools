import numbers
import numpy as np
import pickle
from collections.abc import Iterable

class MeasuredData(object):
    """Objects to stored measured or computed values"""

    def load(file_name):
        """Load data from a saved object.

        NOTE: the loaded object will be an instance of MeasuredData.

        """
        with open(file_name, 'rb') as file_:
            obj = pickle.load(file_)
        return obj

    def __init__(self):
        self._data = {'space': [None, None], 'time': None, 'results': None}
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
        if self._steps['time'] is None:
            return None
        else:
            return self._steps['time'][0]

    @fs.setter
    def fs(self, value):
        self._set_steps('freq', value)

    @property
    def dt(self):
        """the time step"""
        if self._steps['time'] is None:
            return None
        else:
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

    @data.setter
    def data(self, values):
        if not isinstance(values, np.ndarray):
            raise TypeError('the values should be a numpy.nparray')
        self._data['results'] = values

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
        return self._data['space'][0]

    @x_vect.setter
    def x_vect(self, values):
        err = TypeError('the values should be a 1D numpy.ndarray')
        if not isinstance(values, np.ndarray):
            raise err
        if len(values.shape) != 1:
            raise err

        self._data['space'][0] = values

    @property
    def y_vect(self):
        """a vector of the discretization of space in the y direction"""
        return self._data['space'][1]

    @y_vect.setter
    def y_vect(self, values):
        err = TypeError('the values should be a 1D numpy.ndarray')
        if not isinstance(values, np.ndarray):
            raise err
        if len(values.shape) != 1:
            raise err

        self._data['space'][1] = values

    def save(self, file_name):
        """Save data from current object to a binary file.

        If the object being saved is an instance of a subclass of
        MeasuredData, it will be an instance of MeasuredData after
        being reloaded, and not of the original class.

        NOTE: this method always overwrite existing files.

        Parameters:
        file_name : str
            The name of the file where the data will be stored.

        """
        obj = MeasuredData()
        for key in obj.__dict__.keys():
            obj.__dict__[key] = self.__dict__[key]

        # Guarantee that the data saved is real not complex
        obj._data['results'] = self.data

        with open(file_name, 'wb') as file_:
            pickle.dump(obj, file_, pickle.HIGHEST_PROTOCOL)

class BaseWave(MeasuredData):
    """Base class to define Wavepacket and Surface"""

    @property
    def space_boundary(self):
        """the limits of the space domain"""
        raise NotImplementedError

    @space_boundary.setter
    def space_boundary(self, L):
        raise NotImplementedError

    @property
    def time_boundary(self):
        """the limits of the time domain"""
        return self._tlim

    @time_boundary.setter
    def time_boundary(self, value):
        if value is None:
            self._tlim = None
            return

        # Recursively try again
        if not isinstance(value, tuple):
            self.time_boundary = (0, value)
            return

        new_values = []
        for v in value:
            if not isinstance(v, numbers.Number):
                raise TypeError('the values for time boundary should \
be numbers')
            else:
                new_values.append(v)
        else:
            self._tlim = (new_values[0], new_values[1])

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

    def eval(self):
        raise NotImplementedError

    def _discretize(self, lims, step, values):
        """Check if values change or not and rediscretize"""
        v1, v2 = lims
        if values is not None:
            if (step == values[1] - values[0] and
                values[0] == v1 and
                values[-1] == v2):
                return values

        # If check fails, re-evaluate
        # Due to floating point errors, to avoid changes in size of
        # the output, I add a quarter of the step to the upper limit
        return np.arange(v1, v2 + step / 4, step)

