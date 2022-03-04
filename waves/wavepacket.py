from numpy import pi
from collections.abc import Iterable
import numpy as np
import waves.base as base

class Wavepacket:
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
    envelope : function of in paramenter, optional, default: None
        The envelope of the resulting vibration.  Should be a fucntion
        `f(x)` of one parameter that take the position `x` in meters
        and returns a factor that will be multiplied to the amplitude
        of the wavepacket at that position.  The envelope is applied
        after normalization.

    """

    def __init__(self, disprel, dx = None, L = None, fs = None, \
                 T = None, freq = None, normalize = True, envelope = None):
        # Parameters for discretization
        self.fs = fs            # Sampling frequency
        self.spectrum = freq    # Frequency spectrum
        self.dx = dx            # Spatial pace
        self.envelope = envelope   # Envelope
        self._data = {'xs': None,  # Space discretization
                      'ts': None,  # Time discretization
                      'ys': None}  # Result

        self.time = T
        self.domain = L
        self.dispersion = disprel
        self.normalize = normalize

    @property
    def normalize(self):
        """flag for noramlization of values"""
        return self._normalize_flag

    @normalize.setter
    def normalize(self, flag):
        # Use if statement to garantee that `normalize` becomes bool
        if flag:
            self._normalize_flag = True
        else:
            self._normalize_flag = False

    @property
    def fs(self):
        """the sampling frequency"""
        if self.dt is None:
            return None
        else:
            return 1/self.dt

    @fs.setter
    def fs(self, fs):
        if fs is None:
            self.dt = None
        else:
            self.dt = 1/fs

    @property
    def domain(self):
        """the limits of the space domain"""
        return self._xlim

    @domain.setter
    def domain(self, L):
        self._xs = None

        if L is None:
            self._xlim = None
            return

        if not isinstance(L, tuple):
            self.domain = (0, L)
        else:
            for i in range(0, 2):
                if not isinstance(L[i], (int, float)):
                    err = 'The limits of the domain should be numbers.'
            self._xlim = (L[0], L[1])

    @property
    def time(self):
        """the limits of the time domain"""
        return self._tlim

    @time.setter
    def time(self, T):
        self._ts = None

        if T is None:
            self._tlim = None
            return

        if not isinstance(T, tuple):
            self._tlim = (0, T)
        else:
            for i in range(0, 2):
                if not isinstance(T[i], (int, float)):
                    err = 'The limits of for the time should be numbers.'
                self._tlim = (T[0], [0])

    @property
    def dispersion(self):
        """a listof the dispersion relationships"""
        return self._disprel

    @dispersion.setter
    def dispersion(self, disprels):
        self._disprel = []
        if isinstance(disprels, Iterable):
            for fun in disprels:
                if not callable(fun):
                    err = '`disprel` should be a callable object, e.g., \
a function of 1 argument, or a list of such elements.'
                    raise TypeError(err)
                else:
                    self._disprel.append(fun)
            return

        elif disprels is None:
            err = 'at least one dispersion relationship is need'
            raise ValueError(err)

        else:
            # Try again
            self.dispersion = [disprels]

    @property
    def spectrum(self):
        """the frequency spectrum as a list of values in hertz"""
        return self._freq_spectrum

    @spectrum.setter
    def spectrum(self, freqs):
        self._freq_spectrum = []
        if isinstance(freqs, Iterable):
            for f in freqs:
                if not isinstance(f, (int, float)):
                    err = '`freqs` should be a number or an iterable, e.g. \
a list, containing the frequency spectrum of the wave packet.'
                    raise TypeError(err)
                else:
                    self._freq_spectrum.append(f)
            return

        elif freqs is None:
            return

        else:
            # Try again
            self.spectrum = [freqs]

    @property
    def envelope(self):
        """the function that generates the envelope"""
        return self._envelope_func

    @envelope.setter
    def envelope(self, func):
        self._envelope_func = None

        if func is None:
            return

        elif not callable(func):
            err = '`envelope` should be a function of one paramenter.'
            raise ValueError(err)

        else:
            self._envelope_func = func
            return

    def get_time(self):
        """Return the discretized time domain."""

        if self.dt is None or self.time is None:
            err = 'Either `fs` or `time` are not set.'
            raise ValueError(err)

        # Return stored values
        t1, t2 = self.time

        # Check with current properties
        if self._ts is not None:
            if (self.dt == self._ts[1] - self._ts[0] and
                self._ts[0] == t1 and
                self._ts[-1] == t2):
                return self._data['ts']

        # If check fails, re-evaluate
        self._data['ts'] = np.arange(t1, t2, self.dt)
        return self._data['ts']

    def get_space(self):
        """Return the discretized space domain."""

        if self.dx is None or self.domain is None:
            err = 'Either `dx` or `domain` are not set.'
            raise ValueError(err)

        # Retrive stored values
        x1, x2 = self.domain

        # Check with current properties
        if self._xs is not None:
            if (self.dx == self._xs[1] - self._xs[0] and
                self._xs[0] == x1 and
                self._xs[-1] == x2):
                return self._data['xs']

        # If check fails, re-evaluate
        self._data['xs'] = np.arange(x1, x2, self.dx)
        return self._data['xs']

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

        if self._data['ys'] is None:
            self.eval()

        return self._data['ys']

    def get_data(self):
        """Return the time history of the wavepacket.

        It does the same as `get_complex_data` but returns a matrix
        with real values.
        """

        # To get 0 displacement at 0 time, we extract the sine part of
        # the data, which is its imaginary part
        return (-np.imag(self.get_complex_data()))

    def purge_data(self):
        """Delete the evaluated data stored in the object."""

        del(self._data)
        self._data = {'xs': None, 'ts': None, 'ys': None}

    def eval(self):
        """Evaluate the wavepacket."""

        # Check if all information is available
        if self.fs is None:
            err = 'the sampling frequency `fs` is not set.'
            raise ValueError(err)
        if self.time is None:
            err = '`time` is not set.'
            raise ValueError(err)
        else:
            self.get_time()
        if self.dx is None:
            err = 'the spatial pace `dx` is not set.'
            raise ValueError(err)
        if self.domain is None:
            err = 'the spatial domain is not set. use set_space()'
            raise ValueError(err)
        else:
            self.get_space()

        data = 0
        for f in self._freq_spectrum:
            for d in self._disprel:
                data += base.complex_wave(d, f,
                                          self._data['xs'],
                                          self._data['ts'])

        # Normalizing
        if self.normalize:
            max_abs = np.max(np.abs(data))
            if max_abs >= 1e-24:
                data /= max_abs

        # Apply envelope
        if callable(self.envelope):
            f = np.vectorize(self.envelope)
            envelope = f(self.get_space())
            for i in range(0, data.shape[0]):
                data[i,:] *= envelope

        self._data['ys'] = data

    def merge(self, wp):
        """Merge spectrum and disperion relationships of a wavepackets.

        The frequency sepctrum and dispersion relationship of a
        wavepacket are added to current object.  Data, however, is not
        merged, and should be recalculated after merge.

        Parameters: wp : Wavepacket
            The wavepacket whose spectrum and disperion relationships
            will be added to current one.
        """

        if not isinstance(wp, wavepacket):
            err = 'the arguments should be `Wavepacket` instances.'
            raise TypeError(err)

        self._freq_spectrum.extend(wp._freq_spectrum)
        self.__disprel.extend(wp.__disprel)
