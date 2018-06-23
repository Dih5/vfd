# -*- coding: utf-8 -*-
"""Mimic matplotlib interface to generate VFD files"""

from __future__ import division

import json
from os import path
import math
import tempfile
import subprocess
from numbers import Number
import logging
import re
from copy import deepcopy

try:
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
except ModuleNotFoundError:
    plt = None

try:
    import itertools.izip as zip
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.Logger("vfd")

try:
    import numpy as np


    def _ensure_normal_type(*lists):
        """Make sure lists of data are regular python"""
        ret = tuple([[] for _ in range(len(lists))])
        for items in zip(*lists):
            if np.isfinite(items).all():
                for pos, i in enumerate(items):
                    if isinstance(i, np.ndarray):
                        i = i.tolist()
                    if isinstance(i, np.generic):
                        ret[pos].append(np.asscalar(i))
                    else:
                        ret[pos].append(i)
        return ret


except ImportError:
    # Assume no numpy is used if no numpy is around
    def _ensure_normal_type(*lists):
        """Make sure lists of data are regular python"""
        ret = tuple([[] for _ in range(len(lists))])
        for items in zip(*lists):
            if any(math.isnan(x) or math.isinf(x) for x in items):
                pass
            else:
                for pos, i in enumerate(items):
                    ret[pos].append(i)
        return ret


def _squeeze_matrix(matrix):
    """Remove dimensions with one element"""
    if len(matrix[0]) == 1 and len(matrix) == 1:
        return matrix[0][0]
    elif len(matrix[0]) == 1:
        return [row[0] for row in matrix]
    elif len(matrix) == 1:
        return matrix[0]
    else:
        return matrix


_float_pattern = '[-+]?(?:(?:\d*\.\d+)|(?:\d+\.?))(?:[Ee][+-]?\d+)?'


def supplant_pyplot():
    """Replace the pyplot module by a Builder instance"""
    import sys
    module = sys.modules['matplotlib']
    module.pyplot = Builder()
    sys.modules['matplotlib'] = module


# TODO: A lot of repeated code to move to a default Axes object

class Builder:
    """
    Class that mimics the behaviour of matplotlib.pyplot to produce vfd files.

    Consider calling the supplant_pyplot method or adding "plt=Builder()" to your plotting script to add vfd file
    generation.

    """

    def __init__(self, to_matplotlib=True):
        """

        Args:
            to_matplotlib (bool): Whether to send all methods to matplotlib.pyplot after getting their info.

        """
        self.data = {}
        self._fig = None
        self._subplots = None
        if plt is None and to_matplotlib:
            logger.warning("Matplotlib not available")
            self.to_matplotlib = False
        else:
            self.to_matplotlib = to_matplotlib

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def semilogx(self, *args, **kwargs):
        self.data["xlog"] = True
        self._plot(*args, **kwargs)
        if self.to_matplotlib:
            return plt.semilogx(*args, **kwargs)

    def semilogy(self, *args, **kwargs):
        self.data["ylog"] = True
        self._plot(*args, **kwargs)
        if self.to_matplotlib:
            return plt.semilogy(*args, **kwargs)

    def loglog(self, *args, **kwargs):
        self.data["xlog"] = True
        self.data["ylog"] = True
        self._plot(*args, **kwargs)
        if self.to_matplotlib:
            return plt.loglog(*args, **kwargs)

    def plot(self, *args, **kwargs):
        self._plot(*args, **kwargs)
        if self.to_matplotlib:
            return plt.plot(*args, **kwargs)

    def _plot(self, *args, **kwargs):
        self.data["type"] = "plot"
        if len(args) == 0:
            raise TypeError("At least one argument is needed")
        new_series = {}
        if len(args) == 1:
            new_series["y"] = _ensure_normal_type(args[0])[0]
        else:
            new_series["x"], new_series["y"] = _ensure_normal_type(args[0], args[1])
        if "label" in kwargs:
            new_series["label"] = kwargs["label"]

        if "series" not in self.data:
            self.data["series"] = [new_series]
        else:
            self.data["series"].append(new_series)

    def errorbar(self, x, y, yerr=None, xerr=None, **kwargs):
        self.data["type"] = "plot"
        new_series = {"x": x, "y": y}
        if yerr:
            if isinstance(yerr, Number):
                new_series["yerr"] = _ensure_normal_type([yerr] * len(y))[0]
            elif isinstance(yerr[0], Number):
                new_series["yerr"] = _ensure_normal_type(yerr)[0]
            else:
                new_series["ymax"] = _ensure_normal_type([y0 + err for y0, err in zip(y, yerr[0])])[0]
                new_series["ymin"] = _ensure_normal_type([y0 - err for y0, err in zip(y, yerr[1])])[0]

        if xerr:
            if isinstance(xerr, Number):
                new_series["xerr"] = _ensure_normal_type([xerr] * len(x))[0]
            elif isinstance(xerr[0], Number):
                new_series["xerr"] = _ensure_normal_type(xerr)[0]
            else:
                new_series["xmax"] = _ensure_normal_type([y0 + err for y0, err in zip(x, xerr[0])])[0]
                new_series["xmin"] = _ensure_normal_type([y0 - err for y0, err in zip(x, xerr[1])])[0]

        if "label" in kwargs:
            new_series["label"] = kwargs["label"]

        if "series" not in self.data:
            self.data["series"] = [new_series]
        else:
            self.data["series"].append(new_series)

        if self.to_matplotlib:
            return plt.errorbar(x, y, yerr=None, xerr=None, **kwargs)

    def xlabel(self, label, **kwargs):
        self.data["xlabel"] = label
        if self.to_matplotlib:
            return plt.xlabel(label, **kwargs)

    def ylabel(self, label, **kwargs):
        self.data["ylabel"] = label
        if self.to_matplotlib:
            return plt.ylabel(label, **kwargs)

    def title(self, title, *args):
        self.data["title"] = title
        if self.to_matplotlib:
            return plt.title(title, *args)

    def legend(self, *args, **kwargs):
        try:
            self.data["legendtitle"] = kwargs["title"]
        except KeyError:
            pass
        # TODO: Parse other args.
        if self.to_matplotlib:
            return plt.legend(*args, **kwargs)

    def ylim(self, *args, **kwargs):
        if len(args) == 2:
            self.data["yrange"] = args
        elif len(args) == 1:
            self.data["yrange"] = args[0]
        # TODO: Parse kwargs
        if self.to_matplotlib:
            return plt.ylim(*args, **kwargs)
        pass

    def xlim(self, *args, **kwargs):
        if len(args) == 2:
            self.data["xrange"] = args
        elif len(args) == 1:
            self.data["xrange"] = args[0]
        # TODO: Parse kwargs
        if self.to_matplotlib:
            return plt.xlim(*args, **kwargs)
        pass

    def contour(self, *args, **kwargs):
        self._colorplot(*args, **kwargs)
        if self.to_matplotlib:
            return plt.contour(*args, **kwargs)

    def contourf(self, *args, **kwargs):
        self._colorplot(*args, **kwargs)
        if self.to_matplotlib:
            return plt.contourf(*args, **kwargs)

    def pcolor(self, *args, **kwargs):
        self._colorplot(*args, **kwargs)
        if self.to_matplotlib:
            return plt.pcolor(*args, **kwargs)

    def pcolormesh(self, *args, **kwargs):
        self._colorplot(*args, **kwargs)
        if self.to_matplotlib:
            return plt.pcolormesh(*args, **kwargs)

    def _colorplot(self, *args, **kwargs):
        if len(args) in [1, 2]:  # 2nd argument might be in the signature of contour/contourf
            self.data["type"] = "colorplot"
            self.data["z"] = list(_ensure_normal_type(*args[0]))
        elif len(args) in [3, 4]:  # 4th argument might be in the signature of contour/contourf
            x, y, z = args[0:3]
            # Dimensions of X,Y in pcolor/pcolormesh might be those of Z + 1 (in fact, they should)
            # Use an average if that is the case
            if len(x) == len(z[0]) + 1:
                x = [(a + b) / 2 for a, b in zip(x[1:], x[:-1])]

            if len(y) == len(z) + 1:
                y = [(a + b) / 2 for a, b in zip(y[1:], y[:-1])]

            self.data["type"] = "colorplot"
            # TODO: Nan and Inf should be improved
            self.data["x"] = _ensure_normal_type(x)[0]
            self.data["y"] = _ensure_normal_type(y)[0]
            self.data["z"] = list(_ensure_normal_type(*z))
        else:
            raise ValueError("Bad argument number")
        if "norm" in kwargs and plt is not None:
            # Check if logarithmic
            if isinstance(kwargs["norm"], LogNorm):
                self.data["zlog"] = True

    def subplots(self, *args, **kwargs):
        # Default values
        num_rows, num_cols = 1, 1
        if len(args) > 0:
            num_rows = args[0]
        if len(args) > 1:
            num_cols = args[1]
        # We allow collision between args and kwargs. It's a feature, not a bug.
        try:
            num_rows = kwargs["nrows"]
        except KeyError:
            pass
        try:
            num_cols = kwargs["ncols"]
        except KeyError:
            pass
        squeeze = True
        try:
            squeeze = kwargs["squeeze"]
        except KeyError:
            pass

        if self.to_matplotlib:
            # To ease treatment
            kwargs["squeeze"] = False
            fig, mpl_axes = plt.subplots(*args, **kwargs)
            self._fig = FigureBuilder(self, fig=fig)
            self._subplots = [[AxesBuilder(axis) for axis in row] for row in mpl_axes]
        else:
            fig = FigureBuilder(self, fig=None)
            self._subplots = [[AxesBuilder(None) for _ in range(num_cols)] for _ in range(num_rows)]
        self.data["type"] = "multiplot"
        try:
            self.data["xshared"] = kwargs["sharex"] if isinstance(kwargs["sharex"], str) else (
                "all" if kwargs["sharex"] else "none")
        except KeyError:
            pass
        try:
            self.data["yshared"] = kwargs["sharey"] if isinstance(kwargs["sharey"], str) else (
                "all" if kwargs["sharey"] else "none")
        except KeyError:
            pass
        if squeeze:
            return self._fig, _squeeze_matrix(self._subplots)
        else:
            return self._fig, self._subplots

    def text(self, x, y, s, **kwargs):
        if "epilog" not in self.data:
            self.data["epilog"] = []
        self.data["epilog"].append({"type": "text", "x": x, "y": y, "text": s})
        if self.to_matplotlib:
            return plt.text(x, y, s, **kwargs)

    def get_data(self):
        if self._subplots is not None:
            self.data["plots"] = [[x.get_data() for x in row] for row in self._subplots]

        return self.data

    def to_json(self, compact=False, compact_arrays=True):
        """
        Return a JSON representation of the data.

        Args:
            compact (bool): Whether to save space in detriment of readability.
            compact_arrays (bool): If compact was False, whether to make 1d arrays of numbers compact.
                                   This both improves readability and saves space.

        Returns:
            str: A JSON representation of the data.

        """
        if compact:
            my_json = json.dumps(self.get_data(), sort_keys=True, separators=(',', ':'))
        else:
            my_json = json.dumps(self.get_data(), sort_keys=True, indent=4, separators=(',', ': '))
            if compact_arrays:
                # numbers in an array should join in one line
                # "number   ,  " into "number,":
                my_json = re.sub(r"(%s)\s*([,\]])\s*" % _float_pattern, r"\g<1>\g<2>", my_json)
                # "[   number  " into "[number":
                my_json = re.sub(r"\[\s*(%s)\s*" % _float_pattern, r"[\g<1>", my_json)
                # "  number   ]" into "number]":
                my_json = re.sub(r"\s*(%s)\s*\]" % _float_pattern, r"\g<1>]", my_json)
        return my_json

    def show(self):
        # TODO: Doesn't work from Jupyter
        with tempfile.NamedTemporaryFile(suffix=".vfd") as f:
            self.savevfd(f.name)
            # Prefer the system installed vfd to the package
            proc = subprocess.Popen(["vfd", path.abspath(f.name)],
                                    cwd=path.abspath(path.dirname(f.name)))
            proc.wait()
        if self.to_matplotlib:
            return plt.show()

    def savevfd(self, fname):
        """
        Save the data as a vfd file.

        This method is automatically called when savefig is called, so whenever an image is exported, so it is the VFD.
        However, the original export is not overridden by the created VFD.

        Args:
            fname: Path where the file will be saved. If the extension is not vfd, it will be changed to it.


        """
        if "." in path.basename(fname):  # If has an extension
            fname = fname.rsplit(".", 1)[0]  # Remove it

        fname += ".vfd"

        with open(fname, "w") as text_file:
            text_file.write(self.to_json())

    def savefig(self, fname, **kwargs):
        self.savevfd(fname)

        if self.to_matplotlib:
            return plt.savefig(fname, **kwargs)

    def __getattr__(self, name):
        if self.to_matplotlib:
            logger.warning("Attribute '%s' is not parsed by Builder" % name)
            return getattr(plt, name)

        else:
            raise AttributeError("Builder has no attribute '%s'" % name)


class FigureBuilder:
    """
    Class that mimics the behaviour of matplotlib.pyplot.figure to produce vfd files.
    """

    def __init__(self, builder, fig=None):
        self.builder = builder
        self.fig = fig

    def savefig(self, fname, **kwargs):
        self.builder.savevfd(fname)

        if self.fig is not None:
            return self.fig.savefig(fname, **kwargs)

    def __getattr__(self, name):
        if self.fig is not None:
            logger.warning("Attribute '%s' is not parsed by FigureBuilder" % name)
            return getattr(self.fig, name)

        else:
            raise AttributeError("FigureBuilder has no attribute '%s'" % name)


class AxesBuilder:
    """
    Class that mimics the behaviour of matplotlib.pyplot.axes to produce vfd files.
    """

    def __init__(self, axes=None):
        self.axes = axes
        self.data = {"type": "plot"}
        self.twins_x = []
        self.twins_y = []

    def plot(self, *args, **kwargs):
        self._plot(*args, **kwargs)
        if self.axes is not None:
            return self.axes.plot(*args, **kwargs)

    def semilogx(self, *args, **kwargs):
        self.data["xlog"] = True
        self._plot(*args, **kwargs)
        if self.axes is not None:
            return self.axes.semilogx(*args, **kwargs)

    def semilogy(self, *args, **kwargs):
        self.data["ylog"] = True
        self._plot(*args, **kwargs)
        if self.axes is not None:
            return self.axes.semilogy(*args, **kwargs)

    def loglog(self, *args, **kwargs):
        self.data["xlog"] = True
        self.data["ylog"] = True
        self._plot(*args, **kwargs)
        if self.axes is not None:
            return self.axes.loglog(*args, **kwargs)

    def errorbar(self, x, y, yerr=None, xerr=None, **kwargs):
        self.data["type"] = "plot"
        new_series = {"x": x, "y": y}
        if yerr:
            if isinstance(yerr, Number):
                new_series["yerr"] = _ensure_normal_type([yerr] * len(y))[0]
            elif isinstance(yerr[0], Number):
                new_series["yerr"] = _ensure_normal_type(yerr)[0]
            else:
                new_series["ymax"] = _ensure_normal_type([y0 + err for y0, err in zip(y, yerr[0])])[0]
                new_series["ymin"] = _ensure_normal_type([y0 - err for y0, err in zip(y, yerr[1])])[0]

        if xerr:
            if isinstance(xerr, Number):
                new_series["xerr"] = _ensure_normal_type([xerr] * len(x))[0]
            elif isinstance(xerr[0], Number):
                new_series["xerr"] = _ensure_normal_type(xerr)[0]
            else:
                new_series["xmax"] = _ensure_normal_type([y0 + err for y0, err in zip(x, xerr[0])])[0]
                new_series["xmin"] = _ensure_normal_type([y0 - err for y0, err in zip(x, xerr[1])])[0]

        if "label" in kwargs:
            new_series["label"] = kwargs["label"]

        if "series" not in self.data:
            self.data["series"] = [new_series]
        else:
            self.data["series"].append(new_series)

        if self.axes is not None:
            return self.axes.errorbar(x, y, yerr=None, xerr=None, **kwargs)

    def _plot(self, *args, **kwargs):
        if len(args) == 0:
            raise TypeError("At least one argument is needed")
        new_series = {}
        if len(args) == 1:
            new_series["y"] = _ensure_normal_type(args[0])[0]
        else:
            new_series["x"], new_series["y"] = _ensure_normal_type(args[0], args[1])
        if "label" in kwargs:
            new_series["label"] = kwargs["label"]

        if "series" not in self.data:
            self.data["series"] = [new_series]
        else:
            self.data["series"].append(new_series)

    def set_xlabel(self, label, **kwargs):
        self.data["xlabel"] = label
        if self.axes is not None:
            return self.axes.set_xlabel(label, **kwargs)

    def set_ylabel(self, label, **kwargs):
        self.data["ylabel"] = label
        if self.axes is not None:
            return self.axes.set_ylabel(label, **kwargs)

    def set_title(self, title, *args):
        self.data["title"] = title
        if self.axes is not None:
            return self.axes.set_title(title, *args)

    def legend(self, *args, **kwargs):
        try:
            self.data["legendtitle"] = kwargs["title"]
        except KeyError:
            pass
        # TODO: Parse other args.
        if self.axes is not None:
            return self.axes.legend(*args, **kwargs)

    def set_ylim(self, *args, **kwargs):
        if len(args) == 2:
            self.data["yrange"] = args
        elif len(args) == 1:
            self.data["yrange"] = args[0]
        # TODO: Parse kwargs
        if self.axes is not None:
            return self.axes.set_ylim(*args, **kwargs)
        pass

    def set_xlim(self, *args, **kwargs):
        if len(args) == 2:
            self.data["xrange"] = args
        elif len(args) == 1:
            self.data["xrange"] = args[0]
        # TODO: Parse kwargs
        if self.axes is not None:
            return self.axes.set_xlim(*args, **kwargs)
        pass

    def contour(self, *args, **kwargs):
        self._colorplot(*args, **kwargs)
        if self.axes is not None:
            return self.axes.contour(*args, **kwargs)

    def contourf(self, *args, **kwargs):
        self._colorplot(*args, **kwargs)
        if self.axes is not None:
            return self.axes.contourf(*args, **kwargs)

    def pcolor(self, *args, **kwargs):
        self._colorplot(*args, **kwargs)
        if self.axes is not None:
            return self.axes.pcolor(*args, **kwargs)

    def pcolormesh(self, *args, **kwargs):
        self._colorplot(*args, **kwargs)
        if self.axes is not None:
            return self.axes.pcolormesh(*args, **kwargs)

    def _colorplot(self, *args, **kwargs):
        if len(args) in [1, 2]:  # 2nd argument might be in the signature of contour/contourf
            self.data["type"] = "colorplot"
            self.data["z"] = _ensure_normal_type(args[0])[0]
        elif len(args) in [3, 4]:  # 4th argument might be in the signature of contour/contourf
            x, y, z = args[0:3]
            # Dimensions of X,Y in pcolor/pcolormesh might be those of Z + 1 (in fact, they should)
            # Use an average if that is the case
            if len(x) == len(z[0]) + 1:
                x = [(a + b) / 2 for a, b in zip(x[1:], x[:-1])]

            if len(y) == len(z) + 1:
                y = [(a + b) / 2 for a, b in zip(y[1:], y[:-1])]

            self.data["type"] = "colorplot"
            self.data["x"] = _ensure_normal_type(x)[0]
            self.data["y"] = _ensure_normal_type(y)[0]
            self.data["z"] = _ensure_normal_type(z)[0]
        else:
            raise ValueError("Bad argument number")
        if "norm" in kwargs and plt is not None:
            # Check if logarithmic
            if isinstance(kwargs["norm"], LogNorm):
                self.data["zlog"] = True

    def text(self, x, y, s, **kwargs):
        if "epilog" not in self.data:
            self.data["epilog"] = []
        self.data["epilog"].append({"type": "text", "x": x, "y": y, "text": s})
        if self.axes is not None:
            return self.axes.text(x, y, s, **kwargs)

    def twinx(self):
        if self.axes is not None:
            new_axis = AxesBuilder(self.axes.twinx())
        else:
            new_axis = AxesBuilder

        self.twins_x.append(new_axis)
        return new_axis

    def twiny(self):
        if self.axes is not None:
            new_axis = AxesBuilder(self.axes.twiny())
        else:
            new_axis = AxesBuilder

        self.twins_y.append(new_axis)
        return new_axis

    def get_data(self):
        data2 = deepcopy(self.data)
        if "series" not in data2:
            data2["series"] = []
        for a in self.twins_x:
            data_twin = a.get_data()
            for s in data_twin["series"]:
                data2["series"].append(deepcopy(s))
                data2["series"][-1]["yadded"] = 1
            # The following code does not account for multiple axes addition
            if "yadded" not in data2:
                data2["yadded"] = [{}]
            if "ylabel" in data_twin:
                data2["yadded"][-1]["label"] = data_twin["ylabel"]
            if "ylog" in data_twin:
                data2["yadded"][-1]["log"] = data_twin["ylog"]
            if "yrange" in data_twin:
                data2["yadded"][-1]["range"] = data_twin["yrange"]

        for a in self.twins_y:
            data_twin = a.get_data()
            for s in data_twin["series"]:
                data2["series"].append(deepcopy(s))
                data2["series"][-1]["xadded"] = 1
            # The following code does not account for multiple axes addition
            if "xadded" not in data2:
                data2["xadded"] = [{}]
            if "xlabel" in data_twin:
                data2["xadded"][-1]["label"] = data_twin["xlabel"]
            if "ylog" in data_twin:
                data2["xadded"][-1]["log"] = data_twin["xlog"]
            if "xrange" in data_twin:
                data2["xadded"][-1]["range"] = data_twin["xrange"]

        return data2

    def __getattr__(self, name):
        if self.axes is not None:
            logger.warning("Attribute '%s' is not parsed by AxesBuilder" % name)
            return getattr(self.axes, name)

        else:
            raise AttributeError("AxesBuilder has no attribute '%s'" % name)
