import copy
import numpy as np
import waves.base as base
import waves.wavepacket as wp
from waves.BaseWave import BaseWave
from collections.abc import Iterable

class Membrane(BaseWave):
    """A class for creating finite vibrating membranes.

    Parameters:
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
    sources : list of (Wavepacket, (float, float)), optional,
        default = None
        The sources of the vibration and their positions.  The sources
        should be objects of the `Wavepacket` class, and the position
        is a tuple (x, y) where `x` and `y` are floats indicating the
        position of the source in the xy-plane.
    normalize : bool, optional, default: True
        Flag do normalize the data.  If True, the maximum amplitude in
        the membrane domain will be 1.
    boundary : string or int, optional, default: 'transparent'
        Sets the boundary conditions of the membrane.  The possible
        string values are: 'free' or 'transparent'.  If set to 'free',
        aditional sources will be added to simulated reflection at the
        boundaries without change of phase of the wave.  If set to
        'transparent', no reflection will be accounted for.  If it is a
        int, it will set the number of iteration to recursively add
        new sources to simulate reflections.

    """

    def __init__(self, fs, dx, size, T,
                 sources = None, normalize = True, boundary = 'transparent'):
        # Parameters for discretization
        self.fs = fs            # Sampling frequency
        self.dx = dx            # Spatial pace
        self.time = T
        self._data = BaseWave()._data
        self.__boundary = boundary
        self.normalize = normalize

        # Describing the domain
        if not isinstance(size, tuple):
            raise ValueError('Membrane: size should be a tuple of floats')
        else:
            self.__Lx = size[0]     # Length in x direction
            self.__Ly = size[1]     # Length in y direction

        # Discretizing the domain
        self.__time = np.arange(self.time[0],
                                self.time[1],
                                1/fs,
                                dtype = np.float32)

        flip_and_hstack = lambda u: (np.hstack((-np.flip(u[1:]), u)))
        xs = flip_and_hstack(np.arange(0, self.__Lx/2, dx,
                                       dtype = np.float32))
        ys = flip_and_hstack(np.arange(0, self.__Ly/2, dx,
                                       dtype = np.float32))
        self._data['domain'] = np.meshgrid(xs, ys)

        # Update Lx and Ly
        self.__Lx = 2 * self.xs[-1]
        self.__Ly = 2 * self.ys[-1]

        # Verify sources
        self.__sources = []
        self.__reflected_sources = []
        if sources is not None:
            if not isinstance(sources, Iterable):
                raise ValueError('Membrane: sources should be a list or None')
            else:
                for src, pos in sources:
                    self.add_source(src, pos)

    @property
    def xs(self):
        return self._data['domain'][0][:,0]

    @property
    def ys(self):
        return self._data['domain'][1][0,:]

    def add_source(self, source, pos):
        """Add a source to the membrane.

        Parameters:
        source : Wavepacket object
        pos: (float, float)
            The (x, y) position of the source

        """

        if not isinstance(source, wp.Wavepacket):
            raise ValueError('Membrane: tuples describing the source \
should have a `Wavepacket` object in the first position')
        if not isinstance(pos, tuple):
            raise ValueError('Membrane: tuples describing the source \
should have a tuple (float, float) in the second position')

        self.__add_source_to_list(source, pos, reflected = False)

        # Check boundary condition
        if self.__boundary == 'transparent':
            return
        elif self.__boundary == 'free' or isinstance(self.__boundary, int):
            # Fist iteration
            reflected_positions = self.__reflect_position(pos)

            # Additional iterations
            if isinstance(self.__boundary, int):
                tmp1 = copy.deepcopy(reflected_positions)
                tmp2 = []

                for k in range(0, self.__boundary - 1):
                    for p in tmp1:
                        tmp2 += self.__reflect_position(p)

                    reflected_positions += tmp2
                    tmp1, tmp2 = tmp2, []

            # Adding to the membrane
            for p in reflected_positions:
                self.__add_source_to_list(source, p, reflected = True)

    def __add_source_to_list(self, source, pos, reflected = False):
        """Add a real or a reflected source."""

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
        dx = self._data['domain'][0] - pos[0]
        dy = self._data['domain'][1] - pos[1]
        dist = np.sqrt(dx ** 2 + dy ** 2)
        d_max = np.max(dist)

        # Check if `pos` is inside the domain of the membrane
        if self.xs[0] <= pos[0] <= self.xs[-1] \
           and self.ys[0] <= pos[1] <= self.ys[-1]:
            d_min = 0
        else:
            d_min = np.min(dist)

        source = copy.deepcopy(source)
        source.purge_data()
        source.dx = self.dx
        source.fs = self.fs
        source.domain = (d_min, d_max)
        source.time = self.time

        if reflected:
            self.__reflected_sources.append((source, pos, dist))
        else:
            self.__sources.append((source, pos, dist))

    def __reflect_position(self, pos):
        """Check the region in which the source is located."""

        # Notation:
        #  0: inside the membrane domain
        #  1 to 8: outside
        #  a to d: the edges of the membrane
        #
        #  1 | 2 | 3 
        # ___|_a_|___
        #    |   |
        #  8 d 0 b 4 
        # ___|_c_|___
        #    |   |
        #  7 | 6 | 5

        x, y = pos
        Dx, Dy = self.__Lx/2, self.__Ly/2
        new_coord = lambda b, p: 2 * b - p
        new_pos = lambda inds: \
            list(map(lambda i:
                     {'a': (x, new_coord(Dy, y)),
                      'b': (new_coord(Dx, x), y),
                      'c': (x, new_coord(-Dy, y)),
                      'd': (new_coord(-Dx, x), y)}[i],
                     inds))

        if (-Dx < x < Dx and
            -Dy < y < Dy):
            # Region 0 -> reflect on [a, b, c, d]
            reflections = new_pos(['a', 'b', 'c', 'd'])

        elif y > Dy and x < - Dx:
            # Region 1 -> reflect on [b, c]
            reflections = new_pos(['b', 'c'])

        elif (y > Dy and
              -Dx <= x < Dx):
            # Region 2 -> reflect on [b, c, d]
            reflections = new_pos(['b', 'c', 'd'])

        elif y > Dy and x >= Dx:
            # Region 3 -> reflect on [c, d]
            reflections = new_pos(['c', 'd'])

        elif (x > Dx and
              -Dy <= y <= Dy):
            # Region 4 -> reflect on [a, c, d]
            reflections = new_pos(['a', 'c', 'd'])

        elif x >= Dx and y <= Dy:
            # Region 5 -> reflect on [a, d]
            reflections = new_pos(['a', 'd'])

        elif y < -Dy and -Dx <= x < Dx:
            # Region 6 -> reflect on [a, b, d]
            reflections = new_pos(['a', 'b', 'd'])

        elif y < -Dy and x < -Dx:
            # Region 7 -> reflect on [a, b]
            reflections = new_pos(['a', 'b'])

        elif (x < -Dx and
              -Dy <= y <= Dy):
            # Region 8 -> reflect on [a, b, c]
            reflections = new_pos(['a', 'b', 'c'])

        else:
            raise ValueError('something went wrong and this condition \
should not have been reached.')

        return reflections

    def eval(self):
        """Evaluate the displacement of the memebrane."""

        data = np.zeros((self.xs.size,
                         self.ys.size,
                         self.__time.size),
                        dtype = np.float32)

        for src, pos, dist in (self.__sources + self.__reflected_sources):
            src.eval()
            src_data = src.get_data()
            src_domain = src.get_space()

            data += base.interp(dist, src_domain, src_data)

            src.purge_data()

        # Normalizing
        if self.normalize:
            max_abs = np.max(np.abs(data))
            if max_abs >= 1e-24:
                data /= max_abs

        self._data['results'] = data

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

        return self._data['results']
