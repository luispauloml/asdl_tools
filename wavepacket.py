import numpy as np
from collections.abc import Iterable

class wavepacket:
    """A class for creating wavepackets in 1D domains."""

    def __init__(self, fs, dx, L, T, disprel, freqs = None):

        # Parameters for discretization
        self.fs = fs            # Sampling frequency
        self.dx = dx            # Spatial pace
        self.dt = 1/fs          # Time pace
        self.__length = L       # Total length of the domain
        self.__period = T       # Total time of travel
        self.__data = None      # Store date

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
            tests = [b for b in map(lambda f: f/dr(f) > cfl/2, \
                                    freqs) if b]
            if not tests == []:
                err = 'at least of the frequencies provided makes the wave exceed the CFL \
condition.'
                raise ValueError(err)
            else:
                self.__frequency_content = freqs

    def get_data(self):
        """Return time history of the wavepacket."""

        if self.__data is None:
            self.eval()

        return self.__data

    def eval(self):
        pass
