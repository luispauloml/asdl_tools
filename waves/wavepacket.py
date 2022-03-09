from numpy import pi
import numbers
import numpy as np
import waves.base as base
from waves.base import BaseWave

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
    L : number or (number, number), optional, default: None
        Length of the domain in [m].  If a tuple is provided, is
        defines the lower and upper limits of the domain.
    fs : number, optional, default: None
        Sampling frequency in [Hz].
    T : number or (number, number), optiona, default: None
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

    def __init__(self, disprel, dx = None, L = None, fs = None, \
                 T = None, freq = None, normalize = True, envelope = None):
        self._data = BaseWave()._data
        self._steps = BaseWave()._steps
        self.fs = fs            # Sampling frequency
        self.spectrum = freq    # Frequency spectrum
        self.dx = dx            # Spatial pace
        self.envelope = envelope   # Envelope
        self.time_boundary = T
        self.space_boundary = L
        self.dispersion = disprel
        self.normalize = normalize

    @property
    def space_boundary(self):
        """the limits of the space domain"""
        return self._xlim

    @space_boundary.setter
    def space_boundary(self, L):
        pred = lambda x: isinstance(x, numbers.Number)
        err = 'The limits of the domain should be numbers.'
        BaseWave._set_tuple_value(self, '_xlim', L, pred,
                                  err, lambda x: x)

    @property
    def dispersion(self):
        """a listof the dispersion relationships"""
        return self._disprel

    @dispersion.setter
    def dispersion(self, disprels):
        predicate = lambda f: callable(f)
        err = '`disprel` should be a callable object, e.g., \
a function of 1 argument, or a list of such elements.'

        def err_if_none():
            err = 'at least one dispersion relationship is need'
            raise ValueError(err)

        BaseWave._set_list_value(self,'_disprel',
                                 disprels, predicate,
                                 err, err_if_none)

    @property
    def spectrum(self):
        """the frequency spectrum as a list of values in hertz"""
        return self._freq_spectrum

    @spectrum.setter
    def spectrum(self, freqs):
        predicate = lambda f: isinstance(f, numbers.Number)
        err = '`freqs` should be a number or an iterable, e.g. \
a list, containing the frequency spectrum of the wave packet.'
        err_if_none = lambda : None

        BaseWave._set_list_value(self, '_freq_spectrum',
                                 freqs, predicate,
                                 err, err_if_none)

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
    def x_vect(self):
        """a vector of the discretization in the x direction"""
        return BaseWave._get_time_or_space(self, 'space')

    @property
    def complex_data(self):
        """the data evaluated in this object in complex values"""
        return self._data['results']

    @property
    def data(self):
        """the data evaluated in this object"""
        if self.complex_data is None:
            return None
        else:
            return (-np.imag(self.complex_data))

    def eval(self):
        """Evaluate the wavepacket."""

        # Rerun discretization
        self.time_vect
        self.x_vect

        data = 0
        for f in self._freq_spectrum:
            for d in self._disprel:
                data += base.complex_wave(d, f,
                                          self._data['domain'],
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
