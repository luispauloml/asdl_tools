# ASDL Tools

This repository contains tools used at the Advanced Structures and
Dynamics Laboratory from the Chonnam National University, in Gwangju,
South Korea.

It contains tools for treating data from vibration experiments.  The
goal of is to provide a standardized way of accessing and storing data
either acquired from test setups of generated by computer.

## Dependencies

This package requires Python 3.7 or newer, and Microsoft Windows 7 or
newer.  This package depends on the following third party packages:

- [Numpy](https://numpy.org/)
- [Scipy](https://scipy.org/)
- [nidaqmx](https://github.com/ni/nidaqmx-python)

It does not depend on Matplotlib, but it is desirable to have it
installed for visualization.

## Installation

To use this package you need [Git](https://git-scm.com) and
[Pip](https://pypi.org/project/pip/) installed in your computer.  To
check whether you already have them installed, go to a Command Prompt
or PowerShell and try these commands:

- for Git: ``git --version``.
- for Pip: ``pip --version`` or ``python -m pip``.

If you use Anaconda as your package management system, you probably
already have Pip installed, and you can use Anaconda itself to install
Git:

    conda install git

If you do not use Anaconda, you will need to find a suitable way of
installing both.  Check their official websites for more information:
- Git: <https://git-scm.com/downloads>
- Pip: <https://pip.pypa.io/en/stable/installation/>

Since this package will have no stable version in the foreseable
future, the best way to install it is by cloning this repository and
installing from a local directory.  First find a suitable location to
have the package downloaded, clone this repository, and install it
using Pip in editable mode.  These commands should work:

	git clone https://github.com/luispauloml/asdl_tools
	cd asdl_tools
	pip install -e .

The last command tells ``pip`` to install the package in current
directory and watch for changes in its files.  This way, in case you
make changes to the files, you will only need to restart your Python
interpreter instead of reinstalling the package.

### Updating

To update the package, go to the ``asdl_tools`` directory and use Git
to pull from origin:

    git pull origin

### A note on the versions of the package

This package loosely follows [Semantic Versioning](https://semver.org),
but it only tracks versions using Git tags instead of always updating
``setup.py`` everytime major changes are made.  Therefore, be aware
that ``pip show asdl_tools`` will always show version 0.0.0.  If you
want to see all the version, look for Git tags:

    git tag

## Usage

You can check the [tutorial](./TUTORIAL.ipynb) for a simple guide on
how to start using this package.  You can also see other examples
[here](./examples/).

After installing, you can import it by doing ``import asdl``.  Be sure
to use Python's ``help`` function to find more information about each
function and method in this package.  Here are important points about
this package:

- The class ``MeasuredData``:

  The most basic functionality of the package, which provides a
  convenient way for saving and loading data.

  You can create a ``MeasuredData`` object, and add attributes to it
  to hold data.  The object can then be saved and loaded as needed:

  ```
  >>> from asdl import MeasuredData, load
  >>> import numpy as np
  >>> a = MeasuredData()
  >>> a.foo = np.array([1, 2, 3])
  >>> a.bar = np.pi
  >>> a.save('baz.pkl')
  >>> b = load('baz.pkl')
  >>> b.foo
  array([1, 2, 3])
  >>> b.bar
  3.141592653589793
  >>> b.bar == np.pi
  True
  ```

  It is also possible to save to and load from MATLAB binary files.
  See ``help(load)`` and ``help(MeasuredData.save)`` for more
  information.

- The ``ni`` sub-package:

  Provides a way for dealing with read (input) and write (output)
  tasks from ``nidaqmx`` package.  This sub-package exists to simplify
  the [``nidaqmx`` package provided by National
  Instruments](https://github.com/ni/nidaqmx-python), that provides
  too much low-level functionality, which can be very confusing when
  using for the first time.  For more information, see the help for
  ``asdl.ni.Task`` and ``asdl.ni.SingleDevice`` classes.
