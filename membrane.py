import numpy as np
from collections.abc import Iterable
import waves.wavepacket as wp

class membrane:
    """A class for creating finite vibrating membranes.

    Parameters:
    sources : list of (wavepacket, (float, float))
        The sources of the vibration and their positions.  The sources
        should be objects of the `wavepacket` class, and the position
        is a tuple (x, y) where `x` and `y` are floats indicating the
        position of the source in the xy-plane.
    fs : float
        Sampling frequency in [Hz].
    dx : float
        Spatial step in meters.
    size : tuple (float, float)
        Size of the membrane in meters. Should be a t (x_size, y_size),
        and the grid is always centered at (0, 0)
    T : float or tuple (float, float)
        Total travel time in [s].  If a tuple is provided, it defines
        the lower and upper limits of the time interval.
    normalize : bool, optional, default: True
        Flag do normalize the data.  If True, the maximum amplitude in
        the membrane domain will be 1.

   """

    def __init__(self, fs, dx, size, T, sources, normalize = True):
        # Parameters for discretization
        self.fs = fs            # Sampling frequency
        self.dx = dx            # Spatial pace
        self.__data = None      # Store data

        # Describing the domain
        if not isinstance(size, tuple):
            raise ValueError('membrane: size should be a tuple of floats')
        else:
            self.__Lx = size[0]     # Length in x direction
            self.__Ly = size[1]     # Length in y direction
        if not isinstance(T, tuple):
            self.__period = (0, T)
        else:
            self.__period = T

        # Discretizing the domain
        self.__time = np.arange(self.__period[0],
                                self.__period[1], 1/fs)

        flip_and_hstack = lambda u: (np.hstack((-np.flip(u[1:]), u)))
        self.__xs = flip_and_hstack(np.arange(0, self.__Lx/2, dx))
        self.__ys = flip_and_hstack(np.arange(0, self.__Ly/2, dx))
        self.__grid = np.meshgrid(self.__xs, self.__ys)

        # Flag for data normalization
        # Use if statement to garantee that `normalize` becomes bool
        if normalize:
            self.__normalize_flag = True
        else:
            self.__normalize_flag = False

        # Verify sources
        if not isinstance(sources, Iterable):
            raise ValueError('membrane: sources should be a list')

        self.__sources = []

        for src, pos in sources:
            if not isinstance(src, wp.wavepacket):
                raise ValueError('membrane: tuples describing the source \
should have a `wavepacket` object in the first position')
            if not isinstance(pos, tuple):
                raise ValueError('membrane: tuples describing the source \
should have a tuple (float, float) in the second position')
            self.__setup_source(src, pos)

    def __setup_source(self, source, pos):
        # To reduce computing time we set the domain of the source
        # as:
        #    - [0, d_max] if the source is inside the membrane
        #    - [d_min, d_max] if the source is outside the
        #      membrane domain
        # where d_min and d_max are the minimum and the maximum
        # distance from the source to the edges of the memebrane
        # Then we interpolate the displacement according to the
        # distance from a point (x, y) to the position of the source.

        # Calculate maximum distance
        dx = self.__grid[0] - pos[0]
        dy = self.__grid[1] - pos[1]
        dist = np.sqrt(dx ** 2 + dy ** 2)
        d_max = np.max(dist)

        # Check if `pos` is inside the domain of the membrane
        if self.__xs[0] <= pos[0] <= self.__xs[-1] \
           and self.__ys[0] <= pos[1] <= self.__ys[-1]:
            d_min = 0
        else:
            d_min = np.min(dist)

        source.dx = self.dx
        source.fs = self.fs
        source.set_space((d_min, d_max))
        source.set_time(self.__period)
        self.__sources.append((source, pos, dist))

    def __getPos(self, coord, shape):
        """Return the position vector or matrix."""

        if coord not in ['x', 'y']:
            raise ValueError("`coord` should be either 'x' or 'y'")
        if shape not in ['vector', 'grid']:
            raise ValueError("`shape` should be either 'vector' or \
'grid'")
        if coord == 'x':
            if coord == 'vector':
                return self.__xs
            else:
                return self.__grid[0]
        else:
            if coord == 'vector':
                return self.__ys
            else:
                return self.__grid[1]

    def getX(self, shape = 'grid'):
        """Return a 2-D matrix with the x coordinates of memebrane.

        Parameters:
        shape : string, optional, default: 'grid'
            If `shape` is 'vector' a vector is returned,
            otherwise, a 2-D matrix is return.

        """

        return self.__getPos('x', shape)

        return self.__grid[0]

    def getY(self, fomart = 'grid'):
        """Return a 2-D matrix with the y coordinates of memebrane.

        Parameters:
        shape : string, optional, default: 'grid'
            If `shape` is 'vector' a vector is returned,
            otherwise, a 2-D matrix is return.

        """

        return self.__getPos('y', shape)

    def eval(self):
        """Evaluate the displacement of the memebrane."""

        data = np.zeros((self.__xs.size, \
                         self.__ys.size, \
                         self.__time.size))

        for src, pos, dist in self.__sources:
            src.eval()
            src_disp = src.get_data()
            src_domain = src.get_space()

            for i, t in enumerate(self.__time):
                data[:,:,i] += np.interp(dist, src_domain, src_disp[i,:])

        self.__data = data

    def get_data(self):
        """Returns the time history of the membrane.

        Returns a matrix of shape (nX, nY, nT) with
            `nT = T * fs`
            `nX = Lx // dx` and
            `nY = Ly // dx`
        where `T` is the total travel time, `fs` is the sampling
        frequency, `Lx` and `Ly` ar the length of the membrane in
        the x and y directions, respectively.  Therefore, each
        page `k` of the matrix is the "photograph" of the
        displacement of the domain in instante `k / fs`.  Each
        element (i, j, k) can be mapped to a position via the
        index (i, j) in the matrices obtained by `getX` and
        `getY` methods.
        """

        return self.__data
