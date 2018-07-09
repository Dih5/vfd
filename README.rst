=============================
Vernacular Figure Description
=============================


.. image:: https://img.shields.io/pypi/v/vfd.svg
        :target: https://pypi.python.org/pypi/vfd

.. image:: https://img.shields.io/travis/Dih5/vfd.svg
        :target: https://travis-ci.org/Dih5/vfd

.. image:: https://readthedocs.org/projects/vfd/badge/?version=latest
        :target: https://vfd.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status




VFD (Vernacular Figure Description) is a JSON-based description system for plots. It aims to describe *what* needs to be
plotted, while *how* it is done is decided when the files are opened. This allows to generate a set of files describing
the plots, which can latter be batch-processed to produce a consistent set of figures.

.. image:: https://github.com/Dih5/vfd/raw/master/demo.png

Also check http://github.com/dih5/vfd/tree/master/external for tools to use it from other applications.


* Free software: LGPLv3+
* Documentation: https://vfd.readthedocs.io.


Features
--------
* Describe and plot:
    * Scatter plots
    * Error bars
    * Color maps (from arrays of 2D data)
    * Multiple plots in one file
    * Two *x* or *y* axes in the same plot
* GUI, CLI and python package to plot the files with matplotlib.
* API mimicking matplotlib's to generate files without changing your code.
* File format will be always backward-compatible. While version < 1.0.0, CLI and API might change.

Instalation
-----------
To install the latest release, assuming you have a Python_ distribution with pip_::

    $ pip install vfd
.. _Python: http://www.python.org/
.. _pip: https://pip.pypa.io/en/stable/installing/

Windows users with no interest in Python might use the deployed installer_ instead.

.. _installer: https://github.com/Dih5/vfd/releases/latest

If you want to enable bash autocompletion add ``eval "$(_VFD_COMPLETE=source vfd)"`` to your ``.bashrc`` file.
