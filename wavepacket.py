import numpy as np
from numpy import pi
from collections.abc import Iterable

class wavepacket:
    """A class for creating wavepackets in 1D domains."""

    def __init__(self, fs, dx, L, T, disprel, freqs = None, normalize = True):

        # Parameters for discretization
        self.fs = fs            # Sampling frequency
        self.dx = dx            # Spatial pace
        self.dt = 1/fs          # Time pace
        self.__length = L       # Total length of the domain
        self.__period = T       # Total time of travel
        self.__data = None      # Store date

        # Flag for data normalization
        # Use if statement to garantee that `normalize` becomes bool
        if normalize:
            self.__normalize_flag = True
        else:
            self.__normalize_flag = False

        # Set dispersion relationship
        self.set_dispersion(disprel)

        # Set frequency spectrum
        self.set_spectrum(freqs)

        # Discretizing the domain
        self.time = np.arange(0, T, 1/fs)
        self.space = np.arange(0, L, dx)

    def set_dispersion(self, disprels):
        """Set the dispersion relationships of the wavepacket."""

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
        """Set the frequency spectrum of the wavepacket."""
        if freqs is None:
            self.__spectrum = None
        elif not isinstance(freqs, Iterable):
            err = '`freqs` should be an iterable, e.g., a list containing the frequency \
spectrum of the wave packet.'
            raise TypeError(err)
        else:
            # Check CFL condition for input parameters 
            cfl = self.dx / self.dt
            
            for d in self.__disprel:
                for f in freqs:
                    if f/d(f) > cfl:
                        err = 'at least of the frequencies provided makes the wave exceed the CFL\
 condition.'
                        raise ValueError(err)

            self.__spectrum = freqs

    def get_complex_data(self):
        """Return the actual data for the wavepacket in complex values."""

        if self.__data is None:
            self.eval()

        return self.__data

    def get_data(self):
        """Return the time history of the wavepacket."""

        # To get 0 displacement at 0 time, we extract the sine part of
        # the data, which is its imaginary part
        return (-np.imag(self.get_complex_data()))

    def eval(self):
        """Evaluate the wavepacket."""

        self.__data = 0
        for f in self.__spectrum:
            for d in self.__disprel:
                self.__data += self.__complex_wave(d, f, self.space,
                                                   self.time)

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
        """Merge spectrum and the dispersion relationships of a wavepacket into current one."""

        if not isinstance(wp, wavepacket):
            err = 'the arguments should be `wavepacket` instances.'
            raise TypeError(err)

        self.__spectrum.extend(wp.__spectrum)
        self.__disprel.extend(wp.__disprel)
