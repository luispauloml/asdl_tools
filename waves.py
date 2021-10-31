#!/bin/python3

import numpy as np
from math import pi

def harmonic_wave(disprel, freq, xs, ts):
    """Return the displacement of a medium as an harmonic wave propagates
    through a medium.

    It returns an array of shape (ts.size, xs.size) with `ts` being
    the vector for the time, and `xs` being the positions in a
    discretized 1D medium.

    `disprel` is the dispersion relationship and it should be a
    function of one argument that takes the linear frequency `freq`
    given in [Hz] and returns the wavenumber in [1/m].

    """

    w = 2*pi*freq               # angular frequency
    k = 2*pi*disprel(freq)      # angular wavenumer
    us = np.zeros((ts.size, xs.size))

    for i in range(0, ts.size):
        ps = k*xs - w*ts[i]
        us[i, :] = (ps <= 0) * np.sin(ps)

    return (-us)
