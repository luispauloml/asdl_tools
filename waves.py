#!/bin/python3

import numpy as np
from math import pi
import scipy.signal.windows as win

def complex_wave(disprel, freq, xs, ts):
    """Return the displacement of a 1D medium due to a 1D complex harmonic wave.

    It returns an array of shape (ts.size, xs.size) with `ts` being
    the vector for the time, and `xs` being the positions in a
    discretized 1D medium.

    The complex harmonic wave is the complex exponential: 
        exp(1j * (k*x - w*t))
    where `k` is the angular wavenumber, `x` is the position, `w` is
    the angular frequency and `t` is the time.

    `disprel` is the dispersion relationship and it should be a
    function of one argument that takes the linear frequency `freq`
    given in [Hz] and returns the wavenumber in [1/m].

    """

    w = 2*pi*freq               # angular frequency
    k = 2*pi*disprel(freq)      # angular wavenumer
    us = np.zeros((ts.size, xs.size), dtype = np.complex128)

    for i in range(0, ts.size):
        ps = k*xs - w*ts[i]
        us[i, :] = (ps <= 0) * np.exp(1j * ps)

    return us

def harmonic_wave(disprel, freq, xs, ts):
    """Return the displacement of a 1D medium due to a 1D sinusoidal wave.

    It is the result of applyting `f(x) = -numpy.imag(x)` to the
    output of `complex_wave`, which extracts the sinus part of it and
    inverts its signal.

    For more information on the other arguments, see
    `help(complex_wave)`.

    """

    return (-np.imag(complex_wave(disprel, freq, xs, ts)))

def wave_packet(disprel, freqs, xs, ts, \
                normalize = True, \
                amplitudes = None):
    """Return the displacement of a 1D medium due to a 1D wave packet.

    It is the result of iterating `complex_wave` over `freqs`, which
    should be a iterable containing the linear frequencies of each
    component of the wave packet.

    If `normalize` is True, the result is normalized by the maximum
    absolute value contained in it.

    If `amplitudes` is not provided, all components will have the
    amplitude equal to one. If it is provided, it should have the same
    length as `freqs`.

    For more information on the other arguments, see
    `help(complex_wave)`.

    """

    us = np.zeros((ts.size, xs.size), dtype = np.complex128)

    if amplitudes is None:
        amplitudes = np.ones((len(freqs),))

    nf = len(freqs)
    for i in range(0, nf):
        us += amplitudes[i] * complex_wave(disprel, freqs[i], xs, ts)

    if normalize:
        return (us / np.max(np.abs(us)))
    else:
        return us

def radial2Dwindow(window, Nx, max_dist, offset = None):
    """Generate a 2D window by revolving a window from scip.signal.windows

The parameters `window` and `Nx` should be the same as those form
`scipy.signal.windows.get_window`. See help for more information.

`max_dist` is the length of the window for interpolation in the target
domain, and `offset` is the value by which the center of the window is
distance from the origin (0,0).

    """
    ws = win.get_window(window, Nx)

    if offset is None:
        offset = 0
    offset = offset - max_dist / 2

    # Unidimensional position for interpolation
    ps = np.linspace(0, max_dist, Nx) + offset

    def filter(x, y):
        p = np.sqrt(x**2 + y**2)
        u = np.interp(p, ps, ws)
        return u

    return (np.vectorize(filter), ws, ps)
