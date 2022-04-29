import csv
import numpy as np
import scipy.io
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
    header = ['-*- Data loaded from a CSV file -*-']
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
    obj.header = header
    obj.x_vect = coords[0][:,0]
    obj.y_vect = coords[1][0,:]
    obj.data = np.squeeze(np.stack(values, axis = 2))
    return obj

def loadmat(file_name):
    """Load MAT file from MATLAB.

    Reads a MAT file generated in MATLAB that contains information
    from laser scan acquired using Junyoung's standard.  The MAT file
    should contain `stc` matrix.  Optional ones are `x`, `real_x`,
    `y`, `real_y`, and `rate`.

    Parameters:
    file_name : str
        The path to the file to be read.

    """
    mat = scipy.io.loadmat(file_name)

    obj = MeasuredData()
    obj.header = ['-*- Data loaded from MATLAB .mat file -*-']
    obj.data = mat['stc']
    dx = None
    dy = None
    for key, val in mat.items():
        if key in ['x', 'real_x']:
            obj.x_vect = np.atleast_1d(np.squeeze(val))
        elif key in ['y', 'real_y']:
            obj.y_vect = np.atleast_1d(np.squeeze(val))
        elif key == 'SR':
            try:
                obj.dx = float(val)
            except:
                pass
        elif key == 'rate':
            try:
                obj.fs = float(val)
            except:
                pass

    # Spatial steps from spatial data
    if obj.dx is not None:
        steps = [None, None]
        for i, vect in enumerate([obj.x_vect, obj.y_vect]):
            if vect is not None and vect.size > 1:
                diff = np.diff(vect)
                delta = np.average(diff)
                if np.argwhere(abs(diff - delta) > 1e-6).size == 0:
                    steps[i] = delta
        if None not in steps:
            if abs(steps[0] - steps[1]) < 1e-6:
                steps = steps[0]
            obj.dx = steps

    return obj

def savemat(file_name, obj, **kwargs):
    """Save an MeasuredData object to MATLAB's MAT file.

    Create a MAT file from a MesauredData object containing
    two-dimensional data.  The values in the resulting MAT file
    corresponds to the object as follows:
    - Nx:   len(obj.x_vect)
    - Ny:   len(obj.y_vect)
    - rate: obj.fs
    - stc:  obj.data or obj.data[:,:,0]
    - x:    obj.x_vect
    - y:    obj.y_vect

    NOTE: only one page of obj.data will be saved.  If obj.data is a
    3D matrix, the first page will be saved; if it is is a 2D matrix,
    the whole data will be saved.

    NOTE: if any value in obj is None, the corresponding value in the
    MAT file will be zero.

    Parameters:
    file_name : str
        Name of the .mat file.
    obj :  MesauredData
        MeasuredData object to be saved
    **kwargs : dict
        Optional arguments to be passed to `scipy.io.savemat`.  For
        more info see `help(scipy.io.savemat)`.

    """
    if not isinstance(obj, MeasuredData):
        raise TypeError('obj should be an instance of MeasuredData')

    # Values that are int in Python (e.g. output of len), should be
    # converted to float for MATLAB, and values numpy.float32 should
    # be cast to numpy.float64
    mdict = dict()
    zip_ = [('Nx', obj.x_vect),
            ('Ny', obj.y_vect),
            ('rate', obj.fs),
            ('stc', obj.data),
            ('x', obj.x_vect),
            ('y', obj.y_vect),
            ('header', obj.header)]
    for key, value in zip_:
        if value is None:
            mdict[key] = 0
        else:
            if isinstance(value, np.ndarray):
                value = value.astype(np.float64)
            if key in ['Nx', 'Ny']:
                value = float(value.size)
            elif key == 'rate':
                # Just a garantee
                value = float(value)
            elif key == 'stc':
                if len(value.shape) == 2:
                    pass
                elif len(value.shape) == 3:
                    value = value[:,:,0]
                else:
                    raise ValueType('the date has incompatible dimensions')
            mdict[key] = value

    return scipy.io.savemat(file_name, mdict, **kwargs)
