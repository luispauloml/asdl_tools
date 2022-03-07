from math import pi
import numpy as np
import numbers
from collections.abc import Iterable

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

class BaseWave:
    """Base class to define Wavepacket and Membrane"""

    def __init__(self):
        self._data = {'domain': None, 'time': None, 'results': None}

    def _set_scalar(self, field, value, apply_to_value, if_none, err):
        dict_ = self.__dict__
        if value is None:
            if_none()
        elif isinstance(value, numbers.Number):
            dict_[field] = apply_to_value(value)
        else:
            raise TypeError(err)

    @property
    def fs(self):
        """the sampling frequency"""
        if self.dt is None:
            return None
        else:
            return 1/self.dt

    @fs.setter
    def fs(self, value):
        err = 'the sampling frequency should be a number.'
        def if_none(obj):
            def worker():
                obj.dt = None
            return worker
        self._set_scalar('dt', value, lambda x: 1/x, if_none(self), err)

    @property
    def dx(self):
        """the step in space"""
        return self._step

    @dx.setter
    def dx(self, value):
        err = 'the step in space should be a number.'
        def if_none(obj):
            def worker():
                obj._step = None
            return worker
        self._set_scalar('_step', value, lambda x: x, if_none(self), err)

    def _set_tuple_value(self, field, value,
                         predicate, err, apply_to_values):
        dict_ = self.__dict__

        if value is None:
            dict_[field] = None
            return

        if not isinstance(value, tuple):
            self._set_tuple_value(field, (0, value), predicate,
                                  err, apply_to_values)
        else:
            new_values = []
            # Use range to guarantee that only two values will be accounted for
            for i in range(0, 2):
                if not predicate(value[i]):
                    raise err
                else:
                    new_values.append(apply_to_values(value[i]))

            dict_[field] = (new_values[0], new_values[1])

    @property
    def domain(self):
        raise NotImplementedError

    @domain.setter
    def domain(self, L):
        raise NotImplementedError

    @property
    def time(self):
        """the limits of the time domain"""
        return self._tlim

    @time.setter
    def time(self, T):
        pred = lambda x: isinstance(x, numbers.Number)
        err = TypeError('The limits of for the time should be numbers.')
        self._set_tuple_value('_tlim', T, pred, err, lambda x: x)

    @property
    def normalize(self):
        """flag for noramlization of values"""
        return self._normalize_flag

    @normalize.setter
    def normalize(self, flag):
        # Use if statement to garantee that `normalize` becomes bool
        if flag:
            self._normalize_flag = True
        else:
            self._normalize_flag = False

    def _set_list_value(self, field, values, predicate, err, if_none):
        dict_ = self.__dict__
        dict_[field] = []
        if isinstance(values, Iterable):
            for v in values:
                if not predicate(v):
                    raise TypeError(err)
                else:
                    dict_[field].append(v)
            return

        elif values is None:
            if_none()

        else:
            self._set_list_value(field, [values], predicate, err, if_none)

    def eval(self):
        raise NotImplementedError

    def purge_data(self):
        """Delete the evaluated data stored in the object."""

        del(self._data)
        self._data = BaseWave()._data

    def _get_time_or_space(self, flag):
        if flag == 'time':
            step, lims = self.dt, '_tlim'
            field, err = 'time', 'Either `fs` or `time` are not set.'
        elif flag == 'space':
            step, lims = self.dx, '_xlim'
            field, err = 'domain', 'Either `dx` or `domain` are not set.'
        else:
            raise ValueError('something went wrong')

        if step is None or self.__dict__[lims] is None:
            raise ValueError(err)

        # Return stored values
        v1, v2 = self.__dict__[lims]
        values = self._data[field]

        # Check with current properties
        if values is not None:
            if (step == values[1] - values[0] and
                values[0] == v1 and
                values[-1] == v2):
                return self._data[field]

        # If check fails, re-evaluate
        self._data[field] = np.arange(v1, v2, step)
        self.__dict__[lims] = (self._data[field][0], self._data[field][-1])
        return self._data[field]

    def get_time(self):
        """Return the discretized time domain."""
        return self._get_time_or_space('time')
