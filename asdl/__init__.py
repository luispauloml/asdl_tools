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
        self._data = {'results': None}
        self.header = []

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
