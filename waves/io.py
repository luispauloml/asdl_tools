import csv
import numpy as np
from .base import MeasuredData

def loadcsv(file_name):
    """Load CSV file exported from COMSOL.

    Reads a CSV file exported from a COMSOL simulation.  The data
    should be two-dimensional with the first and the second columns
    being X and Y position, respectively.  In order to generate proper
    square matrices, the mesh used in COMSOL should be rectangular.

    Parameters:
    file_name : str
        The path to the file to be read.

    """
    file_handler = open(file_name, mode = 'rt')
    header = []
    data = []

    for line in csv.reader(file_handler, delimiter = ' ',
                           skipinitialspace = True):
        if line[0][0] == '%':
            header.append(' '.join(line))
        else:
            data.append([float(v) for v in line])

    data = np.array(data)

    # Sort by first column
    data = data[np.argsort(data[:,0]), :]
    size = np.sqrt(data.shape[0])
    if size - round(size) > 1e-9:
        raise ValueError('the data cannot be reshaped properly')

    # Reshaping
    square_reshape = lambda arr, size: np.reshape(arr, (int(size), int(size)))
    arrays = []
    for arr in (data[:,i] for i in range(data.shape[1])):
        arrays.append(square_reshape(arr, size))

    # Sorting by y-values
    for row in range(arrays[0].shape[0]):
        inds = np.argsort(arrays[1][row,:])
        for i in range(len(arrays)):
            arrays[i][row,:] = arrays[i][row, inds]
    coords = arrays[0:2]
    values = arrays[2:]

    obj = MeasuredData()
    obj.log = header
    obj.x_vect = coords[0][:,0]
    obj.y_vect = coords[1][0,:]
    obj.data = np.squeeze(np.stack(values, axis = 2))
    return obj
