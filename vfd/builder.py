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

    def to_json(self):
        return json.dumps(self.data, sort_keys=True, indent=4, separators=(',', ': '))

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
            logger.warning("Attribute '%s' no parsed by Builder")
            return getattr(plt, name)

        else:
            raise AttributeError("Builder has no attribute '%s'" % name)
