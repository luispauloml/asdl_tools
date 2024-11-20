"""Tools for working at ASDL.

A collection of tools useful for work at the Active Structures and Dynamic
Systems Laboratory.

"""


import os
import pickle
import collections
import time
from typing import Self, Any


__all__ = ['MeasuredData', 'DataCollection', 'load']


class MeasuredData(object):
    """Object to store, save and load data."""

    @staticmethod
    def load(file_name: os.PathLike) -> 'MeasuredData':
        """Load data from a saved object.

        If `file_name` ends with ".mat", try to load a MATLAB binary
        file; if it ends with ".npz", try to load a NumPy ".npz" file.
        Otherwise, try to unpickle a `MeasuredData' object.

        """
        _, ext = os.path.splitext(file_name)
        if ext == '.mat':
            from scipy.io import loadmat  # type: ignore[import-untyped]
            from numpy import squeeze

            mat = loadmat(file_name)
            obj = MeasuredData()
            for k, v in mat.items():
                v = squeeze(v)
                obj.__dict__[k] = v[()] if v.ndim == 0 else v
        elif ext == '.npz':
            from numpy import load as loadz

            obj = MeasuredData()
            with loadz(file_name, allow_pickle=True) as mat:
                for k, v in mat.items():
                    setattr(obj, k, v[()] if v.ndim == 0 else v)
        else:
            with open(file_name, 'rb') as file_:
                obj = pickle.load(file_)
        return obj

    def save(
        self,
        file_name: os.PathLike,
        overwrite: bool = True,
        timestamp: bool = True,
        protocol: int = 4
    ) -> None:
        """Save data from current object to a binary file.

        Parameters:
        file_name :
            The name of the file where the data will be stored.  If
            `file_name` ends with ".mat", save a MATLAB binary file;
            if it ends with ".pkl", save a `MeasuredData` pickled object.
            Otherwise, append extension ".npz" and save NumPy file.
        overwrite :
            If True, overwrite an already existing file.  If False and
            target file already exists, raise `FileExistsError`.
            Default is True.
        timestamp :
            If True, add a time stamp to the object before saving it,
            and if a time stamp already exists, overwrite it.  If
            False, do not create a time stamp, and if it already
            exists, do not modify it.  Default is True.
        protocol :
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
        _, ext = os.path.splitext(file_name)
        if ext == '.mat':
            from scipy.io import savemat

            none_keys = []
            for k, v in self.__dict__.items():
                if v is None:
                    none_keys.append(k)
                    self.__dict__[k] = []
            savemat(file_name, self.__dict__, appendmat=False)
            for k in none_keys:
                self.__dict__[k] = None
        elif ext == '.pkl':
            with open(file_name, 'wb') as file_:
                pickle.dump(self, file_, protocol)
        else:
            from numpy import savez

            savez(file_name, **self.__dict__)

    def copy(self) -> Self:
        """Make a deep copy of the object."""
        import copy

        return copy.deepcopy(self)


class DataCollection(collections.UserList, MeasuredData):
    """A collection of measured data.

    Parameters:
    initlist :
        A list data objects to be saved.
    """
    # `DataCollection` is a subclass of `MeasuredData` so that it can
    # inherit the `save` and `load` methods.  Each entry in
    # `DataCollection` is expected to -- but not required to -- be of
    # type `MeasuredData`.  This looks like a cyclic dependency, but
    # since the only methods defined in `MeasuredData` are `save` and
    # `load`, it (probably) will not be a problem.
    @property
    def last(self) -> Any:
        """the last object in the list"""
        return self[-1]

    @last.setter
    def last(self, value):
        self[-1] = value


load = MeasuredData.load
