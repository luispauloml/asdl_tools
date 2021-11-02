import numpy as np

class wavepacket:
    """A class for creating wavepackets in 1D domains."""

    def __init__(self, fs, dx, L, T, disprel, freqs = None):

        # Parameters for discretization
        self.fs = fs            # Sampling frequency
        self.dx = dx            # Spatial pace
        self.dt = 1/fs          # Time pace
        self.__length = L       # Total length of the domain
        self.__period = T       # Total time of travel

        # Check the dispersion relationship
        if not callable(disprel):
            err = '`disprel` should be a callable object, e.g., a function of 1 \
argument.'
            raise TypeError(err)
        self.__disprel = disprel

        # Check the frequency content
        if freqs is None:
            self.__freqs = None
        elif not isinstance(freqs, collections.abc.Iterable):
            err = '`freqs` should be an iterable, e.g., a list containing the frequency \
contenct of the wave packet.'
            raise TypeError(err)
        else:
            self.__frequency_content = freqs
            self.__check_cfl()

        # Discretizing the domain
        self.time = np.arange(0, T, 1/fs)
        self.space = np.arange(0, L, dx)

    def __check_cfl(self):
        """Check if the parameters meet the CFL condition."""
        pass
