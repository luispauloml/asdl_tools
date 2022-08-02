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
        self.header = []

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

        with open(file_name, 'wb') as file_:
            pickle.dump(obj, file_, pickle.HIGHEST_PROTOCOL)
