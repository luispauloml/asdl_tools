import os
import pickle

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
