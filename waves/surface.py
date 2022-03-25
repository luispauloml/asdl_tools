import copy
import numbers
import numpy as np
from collections.abc import Iterable
from . import base
from . import wavepacket as wp
from .base import BaseWave

class Surface(BaseWave):
    """A class for creating finite vibrating surfaces.

    Parameters:
    fs : float
        Sampling frequency in [Hz].
    dx : float
        Spatial step in meters.
    size : tuple (float, float)
        Dimensions of the surface in meters. Should be a tuple
        (x_size, y_size), and the grid is always centered at (0, 0).
    time : float or tuple (float, float)
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
        the surface domain will be 1.
    boundary : string or int, optional, default: 'transparent'
        Sets the boundary conditions of the surface.  The possible
        string values are: 'free' or 'transparent'.  If set to 'free',
        aditional sources will be added to simulated reflection at the
        boundaries without change of phase of the wave.  If set to
        'transparent', no reflection will be accounted for.  If it is a
        int, it will set the number of iteration to recursively add
        new sources to simulate reflections.

    """

    def __init__(self, fs, dx, size, time,
                 sources = None, normalize = True, boundary = 'transparent'):
        # Parameters for discretization
        self._steps = BaseWave()._steps
        self.fs = fs            # Sampling frequency
        self.dx = dx            # Spatial pace
        self.time_boundary = time
        self.space_boundary = size
        self._data = BaseWave()._data
        self.boundary_condition = boundary
        self.normalize = normalize

        # Describing the domain
        Lx = self.space_boundary[0][1]     # Length in x direction
        Ly = self.space_boundary[1][1]     # Length in y direction

        # Discretizing the domain
        BaseWave._get_time_or_space(self, 'time')

        flip_and_hstack = lambda u: (np.hstack((-np.flip(u[1:]), u)))
        xs = flip_and_hstack(np.arange(0, Lx, dx, dtype = np.float32))
        ys = flip_and_hstack(np.arange(0, Ly, dx, dtype = np.float32))
        self._data['domain'] = np.meshgrid(xs, ys)

        # Update domain
        self.domain = (self.x_vect[-1]*2, self.y_vect[-1]*2)

        # Verify sources
        self._sources = []
        self._reflected_sources = []
        if sources is not None:
            if not isinstance(sources, Iterable):
                raise TypeError('sources should be a list or None')
            else:
                for src, pos in sources:
                    self.add_source(src, pos)

    @property
    def space_boundary(self):
        """the limits of the surface"""
        return self._xylims

    @space_boundary.setter
    def space_boundary(self, value):
        err = TypeError('the size of the surface shoulde be a tuple of \
two numbers greater than 0.')

        if not isinstance(value, tuple):
            raise err

        field = '_xylims'
        pred = lambda x: isinstance(x, numbers.Number) and x > 0
        f = lambda x: (-x/2, x/2)
        BaseWave._set_tuple_value(self, field, value, pred, err, f)

    @property
    def x_vect(self):
        """a vector with the discretization of space in the x direction"""
        return self._data['domain'][0][0,:]

    @property
    def y_vect(self):
        """a vector of the discretization in the y direction"""
        return self._data['domain'][1][:,0]

    @property
    def xy_grid(self):
        """a tuple with the grid of x and y values"""
        return self._data['domain']

    @property
    def time_vect(self):
        """a vector of the discretization of the time"""
        return self._data['time']

    @property
    def boundary_condition(self):
        """the boundary conditions"""
        return self._boundary

    @boundary_condition.setter
    def boundary_condition(self, value):
        if (value in ('transparent', 'free') or
            isinstance(value, int)):
            self._boundary = value
        else:
            raise TypeError("the boundary conditions should be 'free', \
'transparent' or a int value.")

    def add_source(self, source, pos):
        """Add a source to the surface.

        Parameters:
        source : Wavepacket object
        pos: (float, float)
            The (x, y) position of the source

        """

        if not isinstance(source, wp.Wavepacket):
            raise TypeError('tuples describing the source \
should have a `Wavepacket` object in the first position')
        if not isinstance(pos, tuple):
            raise TypeError('tuples describing the source \
should have a tuple (number, number) in the second position')
        if ((not isinstance(pos[0], numbers.Number)) or
            (not isinstance(pos[1], numbers.Number))):
            raise TypeError('the two elements of the \
position should be numbers.')

        self._add_source_to_list(source, pos, reflected = False)

        # Check boundary condition
        if self.boundary_condition == 'transparent':
            return
        elif (self.boundary_condition == 'free' or
              isinstance(self.boundary_condition, int)):
            # Fist iteration
            reflected_positions = self._reflect_position(pos)

            # Additional iterations
            if isinstance(self.boundary_condition, int):
                tmp1 = copy.deepcopy(reflected_positions)
                tmp2 = []

                for k in range(0, self.boundary_condition - 1):
                    for p in tmp1:
                        tmp2 += self._reflect_position(p)

                    reflected_positions += tmp2
                    tmp1, tmp2 = tmp2, []

            # Adding to the surface
            for p in reflected_positions:
                self._add_source_to_list(source, p, reflected = True)

    def _add_source_to_list(self, source, pos, reflected = False):
        """Add a real or a reflected source."""

        # To reduce computing time we set the domain of the source
        # as:
        #    - [0, d_max] if the source is inside the surface
        #    - [d_min, d_max] if the source is outside the
        #      surface domain
        # where d_min and d_max are the minimum and the maximum
        # distance from the source to the edges of the surface
        # Then we interpolate the displacement according to the
        # distance from a point (x, y) to the position of the source.

        # Calculate maximum distance
        dx = self._data['domain'][0] - pos[0]
        dy = self._data['domain'][1] - pos[1]
        dist = np.sqrt(dx ** 2 + dy ** 2)
        d_max = np.max(dist)

        # Check if `pos` is inside the domain of the surface
        if self.x_vect[0] <= pos[0] <= self.x_vect[-1] \
           and self.y_vect[0] <= pos[1] <= self.y_vect[-1]:
            d_min = 0
        else:
            d_min = np.min(dist)

        source = copy.deepcopy(source)
        source.purge_data()
        source.dx = self.dx
        source.fs = self.fs

        # Floating point operations may result in different values
        # between the two classe.  Instead of simply passing
        # time_boundary and (d_min, d_max) to the the source, it is
        # desirable to modify it to avoid the discretization in the
        # source returning one value less than it should be.
        # Therfore, I add a quarter of self.dt and self.dx to the
        # upper limits.
        source.space_boundary = (d_min, d_max + self.dx / 4)
        source.time_boundary = (self.time_boundary[0],
                                self.time_boundary[1] + self.dt / 4)

        if reflected:
            self._reflected_sources.append((source, pos, dist))
        else:
            self._sources.append((source, pos, dist))

    def _reflect_position(self, pos):
        """Check the region in which the source is located."""

        # Notation:
        #  0: inside the surface domain
        #  1 to 8: outside
        #  a to d: the edges of the surface
        #
        #  1 | 2 | 3 
        # ___|_a_|___
        #    |   |
        #  8 d 0 b 4 
        # ___|_c_|___
        #    |   |
        #  7 | 6 | 5

        x, y = pos
        Dx, Dy = self.space_boundary[0][1], self.space_boundary[1][1]
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

        elif (y >= Dy and
              -Dx <= x < Dx):
            # Region 2 -> reflect on [b, c, d]
            reflections = new_pos(['b', 'c', 'd'])

        elif y > Dy and x >= Dx:
            # Region 3 -> reflect on [c, d]
            reflections = new_pos(['c', 'd'])

        elif (x >= Dx and
              -Dy <= y <= Dy):
            # Region 4 -> reflect on [a, c, d]
            reflections = new_pos(['a', 'c', 'd'])

        elif x >= Dx and y <= -Dy:
            # Region 5 -> reflect on [a, d]
            reflections = new_pos(['a', 'd'])

        elif y <= -Dy and -Dx <= x < Dx:
            # Region 6 -> reflect on [a, b, d]
            reflections = new_pos(['a', 'b', 'd'])

        elif y < -Dy and x < -Dx:
            # Region 7 -> reflect on [a, b]
            reflections = new_pos(['a', 'b'])

        elif (x <= -Dx and
              -Dy <= y <= Dy):
            # Region 8 -> reflect on [a, b, c]
            reflections = new_pos(['a', 'b', 'c'])

        else:
            raise ValueError('something went wrong and this condition \
should not have been reached.')

        return reflections

    def eval(self):
        """Evaluate the displacement of the surface."""

        data = np.zeros((self.y_vect.size,
                         self.x_vect.size,
                         self.time_vect.size),
                        dtype = np.float32)

        for src, pos, dist in (self._sources + self._reflected_sources):
            src.eval()

            data += base.interp(dist, src.x_vect, src.data)

            src.purge_data()

        # Normalizing
        if self.normalize:
            max_abs = np.max(np.abs(data))
            if max_abs >= 1e-24:
                data /= max_abs

        self._data['results'] = data

    @property
    def data(self):
        """the data evaluated in this object"""
        return self._data['results']
