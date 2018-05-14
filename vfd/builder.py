from __future__ import division

import json
from os import path
import math
import tempfile
import subprocess
from numbers import Number
import logging

try:
    import matplotlib.pyplot as plt
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


# TODO: A lot of repeated code to move to a default Axes object

class Builder:
    """
    Class that mimics the behaviour of matplotlib.pyplot to produce vfd files.

    An instance can be used as a context manager: "with Builder() as plt:". However, note this overrides your plt
    variable.
    """

    def __init__(self, to_matplotlib=True):
        """

        Args:
            to_matplotlib (bool): Whether to send all methods to matplotlib.pyplot after getting their info.

        """
        self.data = {}
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
        self._colorplot(*args)
        if self.to_matplotlib:
            return plt.contour(*args, **kwargs)

    def contourf(self, *args, **kwargs):
        self._colorplot(*args)
        if self.to_matplotlib:
            return plt.contourf(*args, **kwargs)

    def pcolor(self, *args, **kwargs):
        self._colorplot(*args)
        if self.to_matplotlib:
            return plt.pcolor(*args, **kwargs)

    def pcolormesh(self, *args, **kwargs):
        self._colorplot(*args)
        if self.to_matplotlib:
            return plt.pcolormesh(*args, **kwargs)

    def _colorplot(self, *args):
        if len(args) in [1, 2]:  # 2nd argument might be in the signature of contour/contourf
            self.data["type"] = "colorplot"
            self.data["z"] = args[0]
        elif len(args) in [3, 4]:  # 4th argument might be in the signature of contour/contourf
            x, y, z = args[0:3]
            # Dimensions of X,Y in pcolor/pcolormesh might be those of Z + 1 (in fact, they should)
            # Use an average if that is the case
            if len(x) == len(z[0]) + 1:
                x = [(a + b) / 2 for a, b in zip(x[1:], x[:-1])]

            if len(y) == len(z) + 1:
                y = [(a + b) / 2 for a, b in zip(y[1:], y[:-1])]

            self.data["type"] = "colorplot"
            self.data["x"] = x
            self.data["y"] = y
            self.data["z"] = z
        else:
            raise ValueError("Bad argument number")

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
            self._subplots = [[AxesBuilder(axis) for axis in row] for row in mpl_axes]
        else:
            fig = None
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
            return fig, _squeeze_matrix(self._subplots)
        else:
            return fig, self._subplots

    def get_data(self):
        if self._subplots is not None:
            self.data["plots"] = [[x.data for x in row] for row in self._subplots]

        return self.data

    def to_json(self):
        return json.dumps(self.get_data, sort_keys=True, indent=4, separators=(',', ': '))

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
        if "." in path.basename(fname):  # If has an extension
            fname = fname.rsplit(".", 1)[0]  # Remove it

        fname += ".vfd"

        with open(fname, "w") as text_file:
            text_file.write(self.to_json())

    def savefig(self, fname):
        self.savevfd(fname)

        if self.to_matplotlib:
            return plt.savefig(fname)

    def __getattr__(self, name):
        if self.to_matplotlib:
            logger.warning("Attribute '%s' is not parsed by Builder" % name)
            return getattr(plt, name)

        else:
            raise AttributeError("Builder has no attribute '%s'" % name)


class AxesBuilder:
    def __init__(self, axes=None):
        self.axes = axes
        self.data = {"type": "plot"}

    def plot(self, *args, **kwargs):
        self._plot(*args, **kwargs)
        if self.axes is not None:
            return self.axes.plot(*args, **kwargs)

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
        self._colorplot(*args)
        if self.axes is not None:
            return self.axes.contour(*args, **kwargs)

    def contourf(self, *args, **kwargs):
        self._colorplot(*args)
        if self.axes is not None:
            return self.axes.contourf(*args, **kwargs)

    def pcolor(self, *args, **kwargs):
        self._colorplot(*args)
        if self.axes is not None:
            return self.axes.pcolor(*args, **kwargs)

    def pcolormesh(self, *args, **kwargs):
        self._colorplot(*args)
        if self.axes is not None:
            return self.axes.pcolormesh(*args, **kwargs)

    def _colorplot(self, *args):
        if len(args) in [1, 2]:  # 2nd argument might be in the signature of contour/contourf
            self.data["type"] = "colorplot"
            self.data["z"] = args[0]
        elif len(args) in [3, 4]:  # 4th argument might be in the signature of contour/contourf
            x, y, z = args[0:3]
            # Dimensions of X,Y in pcolor/pcolormesh might be those of Z + 1 (in fact, they should)
            # Use an average if that is the case
            if len(x) == len(z[0]) + 1:
                x = [(a + b) / 2 for a, b in zip(x[1:], x[:-1])]

            if len(y) == len(z) + 1:
                y = [(a + b) / 2 for a, b in zip(y[1:], y[:-1])]

            self.data["type"] = "colorplot"
            self.data["x"] = x
            self.data["y"] = y
            self.data["z"] = z
        else:
            raise ValueError("Bad argument number")

    def __getattr__(self, name):
        if self.axes is not None:
            logger.warning("Attribute '%s' is not parsed by AxesBuilder" % name)
            return getattr(self.axes, name)

        else:
            raise AttributeError("AxesBuilder has no attribute '%s'" % name)
