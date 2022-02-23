import numpy as np
from numpy import pi
from collections.abc import Iterable
from warnings import warn

class wavepacket:
    """A class for creating wavepackets in 1D domains.

    The class simulates a wavepacket in a 1D domain given the
    dispersion relationships of the waves, the discretization
    parameters, i.e., sampling frequency, spacial step, time and
    length of the domain, and the frequency spectrum of the packet.

    Parameters:
    disprel : function or list of functions
        The dispersion relationships of the wavepacket.  Each function
        should take the frequency in hertz and return the wave number
        in [1/m].
    dx : float, optional, default: None
        Spatial step in meters.
    L : float or tuple of float, optional, default: None
        Length of the domain in [m].  If a tuple is provided, is
        defines the lower and upper limits of the domain.
    fs : float, optional, default: None
        Sampling frequency in [Hz].
    T : float or (float, float), optiona, default: None
        Total travel time in [s].  If a tuple is provided, it defines
        the lower and upper limits of the time interval.
    freqs : list of float, optional, default: None
        The frequency spectrum of the wavepacket.  Each element should
        be a frequency in hertz.  If not given, the object cannot
        generate any data.
    normalize : bool, optional, default: True
        Flag to normalize the data.  If True, the maximum amplitude of
        the wavepacket will be 1.

    """

    def __init__(self, disprel, dx = None, L = None, fs = None, \
                 T = None, freqs = None, normalize = True):
        # Parameters for discretization
        self.fs = fs            # Sampling frequency
        self.dx = dx            # Spatial pace
        self.dt = None          # Time pace
        self.__data = None      # Store data

        # Describing the domain
        self.set_time(T)
        self.set_space(L)

        # flag for data normalization
        # Use if statement to garantee that `normalize` becomes bool
        if normalize:
            self.__normalize_flag = True
        else:
            self.__normalize_flag = False

        # Set dispersion relationship
        self.set_dispersion(disprel)

        # Set frequency spectrum
        self.set_spectrum(freqs)

    def set_space(self, L):
        """Set the space domaing for the wavepacket.

        Parameters:
        L : float or (float, float)
          If L is a tuple, it sets the lower and uppper limits of the
          space domain.

        """

        self.__space = None
        if L is None:
            self.__length = None
            return

        if not isinstance(L, tuple):
            self.__length = (0, L)
        else:
            self.__length = L

        if self.dx is not None:
            self.__space = np.arange(self.__length[0],
                                     self.__length[1], self.dx)

    def set_time(self, T):

        """Set the total travel time of the wavepacket.

        Parameters:
        T : float or (float, float)
          If T is a tuple, it sets the lower and upper limits of the
          time interval.

        """

        self.__time = None
        if T is None:
            self.__period = None
            return

        if not isinstance(T, tuple):
            self.__period = (0, T)
        else:
            self.__period = T

        if self.fs is not None:
            self.dt = 1/self.fs
            self.__time = np.arange(self.__period[0],
                                    self.__period[1], self.dt)

    def set_dispersion(self, disprels):
        """Set the dispersion relationships of the wavepacket.

        Changes the dispersion relationships of the object to new
        ones.

        Parameters:
        disprels : function or list of functions
            Each function should take one argument only, which is the
            frequency in hertz and return the wavenumber in [1/m].
        """

        # Put in a list if it is not a list
        if not isinstance(disprels, Iterable):
            disprels = [disprels]

        # Check if elements are collables
        for d in disprels:
            if not callable(d):
                err = '`disprel` should be a callable object, e.g., a function of 1 \
argument, or a list of such elements.'
                raise TypeError(err)

        self.__disprel = disprels

    def set_spectrum(self, freqs):
        """Set the frequency spectrum of the wavepacket.

        Changes the frequency spectrum of the object to new values.

        Parameters:
        freqs : list of float
            A list of frequencies in [Hz].
        """

        if freqs is None:
            self.__spectrum = None
        elif not isinstance(freqs, Iterable):
            err = '`freqs` should be an iterable, e.g., a list containing \
the frequency spectrum of the wave packet.'
            raise TypeError(err)
        elif self.dx is None or self.fs is None:
            err = 'either the sampling frequency `fs` or the spatial pace \
`dx` is not set; CFL condition cannot be checked.'
            warn(err)
            self.__spectrum = freqs
        else:
            # Check CFL condition for input parameters 
            cfl = self.dx / self.dt
            
            for f in freqs:
                if f > self.fs:
                    err = 'at least on of the frequencies is higher than the \
Nyquist frequency.'
                    warn(err)
                for d in self.__disprel:
                    if f/d(f) > cfl:
                        err = 'at least one of the frequencies provided makes \
the wave exceed the CFL condition.'
                        warn(err)

            self.__spectrum = freqs

    def get_time(self):
        """Return the discretized time domain."""

        return self.__time

    def get_space(self):
        """Return the discretized space domain."""

        return self.__space

    def get_complex_data(self):
        """Return the actual data for the wavepacket in complex values.

        Returns a matrix of shape (nT, nX) with
            `nT = T * fs` and `nX = L // dx`,
        where `T` is the total travel time, `fs` is the sampling
        frequency, `L` is the length of the domain and `dx` is spatial
        step.  Therefore, each line `i` of the matrix the displacement
        of the domain in instant `i / fs` seconds, and each column `j`
        is the whole time history from 0 to T of a point in position
        `j * dx`.  If the wavepacket have not been evaluated yet,
        `eval` with be run.
        """

        if self.__data is None:
            self.eval()

        return self.__data

    def get_data(self):
        """Return the time history of the wavepacket.

        It does the same as `get_complex_data` but returns a matrix
        with real values.
        """

        # To get 0 displacement at 0 time, we extract the sine part of
        # the data, which is its imaginary part
        return (-np.imag(self.get_complex_data()))

    def eval(self):
        """Evaluate the wavepacket."""

        # Check if all information is available
        if self.fs is None:
            err = 'the sampling frequency `fs` is not set.'
            raise ValueError(err)
        if self.__time is None:
            err = 'the time interval is not set. use set_time()'
            raise ValueError(err)
        if self.dx is None:
            err = 'the spatial time `dx` is not set.'
            raise ValueError(err)
        if self.__space is None:
            err = 'the spatial domain is not set. use set_space()'
            raise ValueError(err)

        self.__data = 0
        for f in self.__spectrum:
            for d in self.__disprel:
                self.__data += self.__complex_wave(d, f, self.__space,
                                                   self.__time)

        # Normalizing
        if self.__normalize_flag:
            self.__data = self.__data / np.max(np.abs(self.__data))

    def __complex_wave(self, disprel, freq, xs, ts):
        """Return the displacement of a 1D medium due to a 1D complex harmonic wave."""

        w = 2*pi*freq               # angular frequency
        k = 2*pi*disprel(freq)      # angular wavenumer
        us = np.zeros((ts.size, xs.size), dtype = np.complex128)

        for i in range(0, ts.size):
            ps = k*xs - w*ts[i]
            us[i, :] = (ps <= 0) * np.exp(1j * ps)

        return us

    def merge(self, wp):
        """Merge spectrum and disperion relationships of a wavepackets.

        The frequency sepctrum and dispersion relationship of a
        wavepacket are added to current object.  Data, however, is not
        merged, and should be recalculated after merge.

        Parameters: wp : wavepacket
            The wavepacket whose spectrum and disperion relationships
            will be added to current one.
        """

        if not isinstance(wp, wavepacket):
            err = 'the arguments should be `wavepacket` instances.'
            raise TypeError(err)

        self.__spectrum.extend(wp.__spectrum)
        self.__disprel.extend(wp.__disprel)
