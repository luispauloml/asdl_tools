#!/bin/python3

import numpy as np
from math import pi

def complex_wave(disprel, freq, xs, ts):
    """Return the displacement of a 1D medium as a complex harmonic wave
    travels through it.

    It returns an array of shape (ts.size, xs.size) with `ts` being
    the vector for the time, and `xs` being the positions in a
    discretized 1D medium.

    The complex harmonic wave is the complex exponential: 
        exp(1j * (k*x - w*t))
    where `k` is the angular wavenumber, `x` is the
    position, `w` is the angular frequency and `t` is the time.

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
    """Return the displacement of a 1D medium as a sinusoidal wave travels
    through it.

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
    """Return the displacement of a 1D medium as a wave packet travels
    through it.

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
