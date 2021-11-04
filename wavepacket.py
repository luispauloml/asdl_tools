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

        # Check the dispersion relationship
        if not callable(disprel):
            err = '`disprel` should be a callable object, e.g., a function of 1 \
argument.'
            raise TypeError(err)
        self.__disprel = disprel

        # Set frequency content
        self.set_freqs(freqs)

        # Discretizing the domain
        self.time = np.arange(0, T, 1/fs)
        self.space = np.arange(0, L, dx)

    def set_freqs(self, freqs):
        """Set the frequency content of the wavepacket."""
        if freqs is None:
            self.__frequency_content = None
        elif not isinstance(freqs, Iterable):
            err = '`freqs` should be an iterable, e.g., a list containing the frequency \
contenct of the wave packet.'
            raise TypeError(err)
        else:
            # Check CFL condition for input parameters 
            cfl = self.dx / self.dt
            dr = self.__disprel
            tests = [b for b in map(lambda f: f/dr(f) > cfl,
                                    freqs) if b]
            if not tests == []:
                err = 'at least of the frequencies provided makes the wave exceed the CFL \
condition.'
                raise ValueError(err)
            else:
                self.__frequency_content = freqs

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
        for f in self.__frequency_content:
            self.__data += self.__complex_wave(self.__disprel,
                                               f,
                                               self.space,
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


