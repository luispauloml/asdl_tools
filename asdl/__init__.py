import numbers
import numpy as np
import pickle

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
        self.header = []

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
