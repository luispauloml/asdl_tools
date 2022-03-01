from math import pi
import numpy as np
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
    us = np.zeros((ts.size, xs.size), dtype = np.complex64)

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

def interp(matrix, xs, data):
    """Interpolate data over matrix.

    This functions interpolates the values of `data` over `matrix`
    based on the values of `xs`.  It is useful to interplote results
    from `complex_wave` of 2D domains.

    `xs` and `data` should be numpy.array of shapes (n,) and (m,n),
    respectively.  `matrix` should be a numpy.array.  If `matrix` has
    shape (p,) this function will return an array of shape (m,p); if
    it has shape (p,q), the returned value will have shape (p,q,m).

    """

    dims = len(matrix.shape)
    interp_vals = lambda i: np.interp(matrix, xs, data[i,:])
    if dims == 1:
        return_val = np.empty((data.shape[0], matrix.shape[0]))
        for i in range(0, return_val.shape[0]):
            return_val[i,:] = interp_vals(i)

    elif dims == 2:
        return_val = np.empty((matrix.shape[0],
                               matrix.shape[1],
                               data.shape[0]))
        for i in range(0, return_val.shape[2]):
            return_val[:,:,i] = interp_vals(i)

    else:
        raise ValueError('`matrix` can have 1 or 2 dimensions only.')

    return return_val

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