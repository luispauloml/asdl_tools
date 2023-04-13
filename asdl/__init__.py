"""Tools for working at ASDL.

A collection of tools useful for work at the Active Structures and Dynamic
Systems Laboratory.

"""


import os
import pickle
import collections
import scipy.io
import time


__all__ = ['MeasuredData', 'DataCollection']


class MeasuredData(object):
    """Object to store, save and load data."""

    @staticmethod
    def load(file_name):
        """Load data from a saved object."""
        with open(file_name, 'rb') as file_:
            obj = pickle.load(file_)
        return obj

    def save(self, file_name, overwrite=True, timestamp=True, protocol=4):
        """Save data from current object to a binary file.

        Parameters:
        file_name : str
            The name of the file where the data will be stored.  If
            `file_name` ends with ".mat", save a MATLAB binary file.
            In case of saving a to MATLAB binary file, None values are
            converted to an empty matrix.
        overwrite : bool, optional
            If True, overwrite an already existing file.  If False and
            target file already exists, raise `FileExistsError`.
            Default is True.
        timestamp : bool, optional
            If True, add a time stamp to the object before saving it,
            and if a time stamp already exists, overwrite it.  If
            False, do not create a time stamp, and if it already
            exists, do not modify it.  Default is True.
        protocol :  int, optional
            The protocol to be used by the pickler.  Default value is
            4, which is compatible for Python versions 3.4 onwards.
            See `pickle` module for more information

        """

        try:
            os.stat(file_name)
        except FileNotFoundError:
            pass
        else:
            if not overwrite:
                raise FileExistsError(f"file '{file_name}' already exists")
        if timestamp:
            self.timestamp = \
                f"{time.strftime('%a, %d %b %Y %H:%M:%S %z', time.localtime())}"

        if file_name[-4:] == '.mat':
            none_keys = []
            for k, v in self.__dict__.items():
                if v is None:
                    none_keys.append(k)
                    self.__dict__[k] = []
            scipy.io.savemat(file_name,
                             self.__dict__,
                             appendmat=False)
            for k in none_keys:
                self.__dict__[k] = None
        else:
            with open(file_name, 'wb') as file_:
                pickle.dump(self, file_, protocol)


class DataCollection(collections.UserList, MeasuredData):
    """A collection of measured data.

    Parameters:
    initlist : list
        A list data objects to be saved.
    """
    # `DataCollection` is a subclass of `MeasuredData` so that it can
    # inherit the `save` and `load` methods.  Each entry in
    # `DataCollection` is expected to -- but not required to -- be of
    # type `MeasuredData`.  This looks like a cyclic dependency, but
    # since the only methods defined in `MeasuredData` are `save` and
    # `load`, it (probably) will not be a problem.
    @property
    def last(self):
        """the last object in the list"""
        return self[-1]

    @last.setter
    def last(self, value):
        self[-1] = value
