``waves``
=========

This is a simple package for simulating waves in one or two
dimensions.

It contains two classes: ``Wavepacket`` and ``Surface``, for one and
two dimensions, respectively.  A ``Wavepacket`` can calculate the
displacement of a 1-D medium due to a wave based on its dispersion
relationship and frequency spectrum, while a ``Surface`` interpolates
those results to calculate the displacement of a plane surface due to
a point source.  The results are calculated by using complex
exponential functions, which are the analytical solutions to most of
the problems in wave propagation.

Dependencies
~~~~~~~~~~~~

* Numpy.


Installation
~~~~~~~~~~~~

Just clone this repository and use ``pip``: ::

   git clone https://github.com/luispauloml/waves
   cd waves/
   pip install .


Usage
~~~~~

You can use ``help(waves.Wavepacket)`` and ``help(waves.Surface)``.
