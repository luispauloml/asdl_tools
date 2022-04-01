import numbers
import numpy as np
import collections.abc
from . import utils
from .base import BaseWave

class Wavepacket(BaseWave):
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
    dx : number, optional, default: None
        Spatial step in meters.
    length : number or (number, number), optional, default: None
        Length of the domain in [m].  If a tuple is provided, is
        defines the lower and upper limits of the domain.
    fs : number, optional, default: None
        Sampling frequency in [Hz].
    time : number or (number, number), optiona, default: None
        Total travel time in [s].  If a tuple is provided, it defines
        the lower and upper limits of the time interval.
    freqs : list of numbers, optional, default: None
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

    def __init__(self, disprel = None, dx = None, length = None, fs = None, \
                 time = None, freq = None, normalize = True, envelope = None):
        self._data = BaseWave()._data
        self._steps = BaseWave()._steps
        self.fs = fs            # Sampling frequency
        self.spectrum = freq    # Frequency spectrum
        self.dx = dx            # Spatial pace
        self.envelope = envelope   # Envelope
        self.time_boundary = time
        self.space_boundary = length
        self.dispersion = disprel
        self.normalize = normalize

    @property
    def space_boundary(self):
        """the limits of the space domain"""
        return self._xlim

    @space_boundary.setter
    def space_boundary(self, value):
        if value is None:
            self._xlim = None
            return

        # Recursively try again
        if not isinstance(value, tuple):
            self.space_boundary = (0, value)
            return

        for v in value:
            if not isinstance(v, numbers.Number):
                raise TypeError('the boundaries should be numbers')

        self._xlim = (value[0], value[1])

    @property
    def dispersion(self):
        """a listof the dispersion relationships"""
        return self._disprel

    @dispersion.setter
    def dispersion(self, disprels):
        if disprels is None:
            self._disprel = []
            return

        # Recursively try again
        if not isinstance(disprels, collections.abc.Iterable):
            self.dispersion = [disprels]
            return

        new_list = []
        for value in disprels:
            if not callable(value):
                raise TypeError('dispersion relationships should be \
functions of one argument')
            else:
                new_list.append(value)
        else:
            self._disprel = new_list

    @property
    def spectrum(self):
        """the frequency spectrum as a list of values in hertz"""
        return self._freq_spectrum

    @spectrum.setter
    def spectrum(self, freqs):
        if freqs is None:
            self._freq_spectrum = []
            return

        # Recursively try again
        if not isinstance(freqs, collections.abc.Iterable):
            self.spectrum = [freqs]
            return

        new_list = []
        for value in freqs:
            if not isinstance(value, numbers.Number):
                raise TypeError('frequency should be a number')
            else:
                new_list.append(value)
        else:
            self._freq_spectrum = new_list

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
            raise TypeError(err)

        else:
            self._envelope_func = func
            return

    @property
    def complex_data(self):
        """the data evaluated in this object in complex values"""
        return self._data['results']

    @property
    def data(self):
        if self.complex_data is None:
            return None
        else:
            return (-np.imag(self.complex_data))

    def eval(self, domain_only = False):
        """Evaluate the wavepacket.

        Parameters:
        domain_only : bool, optional, default = False
            Evaluate only the discretization of the time and space
            domains.  After evaluating at least the domain, the values
            for `x_vect` and friends are available.

        """

        # Rerun discretization
        self._data['time'] = \
            BaseWave._discretize(self, self.time_boundary, self.dt, self.time_vect)
        self._data['space'][0] = \
            BaseWave._discretize(self, self.space_boundary, self.dx, self.x_vect)
        self.time_boundary = (self.time_vect[0], self.time_vect[-1])
        self.space_boundary = (self.x_vect[0], self.x_vect[-1])

        if domain_only:
            return

        data = np.zeros((self._data['time'].size,
                         self.x_vect.size),
                        dtype = np.complex128)

        for f in self._freq_spectrum:
            for d in self._disprel:
                data += utils.complex_wave(d, f,
                                           self.x_vect,
                                           self._data['time'])

        # Normalizing
        if self.normalize:
            max_abs = np.max(np.abs(data))
            if max_abs >= 1e-24:
                data /= max_abs

        # Apply envelope
        if callable(self.envelope):
            f = np.vectorize(self.envelope, otypes = [np.float32])
            envelope = f(self.x_vect)
            for i in range(0, data.shape[0]):
                data[i,:] *= envelope

        self._data['results'] = data
