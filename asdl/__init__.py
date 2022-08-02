import pickle

class MeasuredData(object):
    """Object to store, save and load data."""

    @staticmethod
    def load(file_name):
        """Load data from a saved object."""
        with open(file_name, 'rb') as file_:
            obj = pickle.load(file_)
        return obj

    def save(self, file_name):
        """Save data from current object to a binary file.

        NOTE: this method always overwrite existing files.

        Parameters:
        file_name : str
            The name of the file where the data will be stored.

        """
        with open(file_name, 'wb') as file_:
            pickle.dump(self, file_, pickle.HIGHEST_PROTOCOL)
