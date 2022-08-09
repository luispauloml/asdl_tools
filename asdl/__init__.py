"""Tools for working at ASDL.

A collection of tools useful for work at the Active Structures and Dynamic
Systems Laboratory.

"""


import os
import pickle
import collections


class MeasuredData(object):
    """Object to store, save and load data."""

    @staticmethod
    def load(file_name):
        """Load data from a saved object."""
        with open(file_name, 'rb') as file_:
            obj = pickle.load(file_)
        return obj

    def save(self, file_name, overwrite=True):
        """Save data from current object to a binary file.

        Parameters:
        file_name : str
            The name of the file where the data will be stored.
        overwrite : bool
            Flag to overwrite an already existing file.

        """

        try:
            os.stat(file_name)
        except FileNotFoundError:
            pass
        else:
            if not overwrite:
                raise FileExistsError(f"file '{file_name}' already exists")

        with open(file_name, 'wb') as file_:
            pickle.dump(self, file_, pickle.HIGHEST_PROTOCOL)


class DataCollection(collections.UserList, MeasuredData):
    """A collection of measured data.

    Parameters:
    list :
        A list data objects to be saved.
    """
    @property
    def last(self):
        """the last object in the list"""
        return self[-1]

    @last.setter
    def last(self, value):
        self[-1] = value
