import json
from os import path
import tempfile
import subprocess

import numpy as np

def _ensure_normal_type(some_list):
    if isinstance(some_list, np.ndarray):
        return some_list.tolist()
    elif isinstance(some_list[0], np.generic):
        return [np.asscalar(x) for x in some_list]
    else:
        return some_list


class Builder:
    """
    Class that mimics the behaviour of matplotlib.pyplot to produce vfd files.

    An instance can be used as a context manager: "with Builder() as plt:".
    """

    def __init__(self):
        self.data = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def semilogx(self, *args, **kwargs):
        self.data["xlog"] = True
        self.plot(*args, **kwargs)

    def semilogy(self, *args, **kwargs):
        self.data["ylog"] = True
        self.plot(*args, **kwargs)

    def loglog(self, *args, **kwargs):
        self.data["xlog"] = True
        self.data["ylog"] = True
        self.plot(*args, **kwargs)

    def plot(self, *args, **kwargs):
        self.data["type"] = "plot"
        if len(args) == 0:
            raise TypeError("At least one argument is needed")
        new_series = {}
        if len(args) == 1:
            new_series["y"] = _ensure_normal_type(args[0])
        else:
            new_series["x"] = _ensure_normal_type(args[0])
            new_series["y"] = _ensure_normal_type(args[1])
        if "label" in kwargs:
            new_series["label"] = kwargs["label"]

        if "series" not in self.data:
            self.data["series"] = [new_series]
        else:
            self.data["series"].append(new_series)

    def xlabel(self, label, **kwargs):
        self.data["xlabel"] = label

    def ylabel(self, label, **kwargs):
        self.data["ylabel"] = label

    def legend(self, *args, **kwargs):
        # TODO: Parse args.
        pass

    def to_json(self):
        return json.dumps(self.data, sort_keys=True, indent=4, separators=(',', ': '))

    def show(self):
        # TODO: Doesn't work from Jupyter
        with tempfile.NamedTemporaryFile(suffix=".vfd") as f:
            self.savefig(f.name)
            # Prefer the system installed vfd to the package
            proc = subprocess.Popen(["vfd", path.abspath(f.name)],
                                    cwd=path.abspath(path.dirname(f.name)))
            proc.wait()

    def savefig(self, fname):
        if "." in path.basename(fname):  # If has an extension
            fname = fname.rsplit(".", 1)[0]  # Remove it

        fname += ".vfd"

        with open(fname, "w") as text_file:
            text_file.write(self.to_json())
