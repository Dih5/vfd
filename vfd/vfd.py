# -*- coding: utf-8 -*-

"""Python API for vfd"""
import json
from glob import glob
import os
import subprocess
from re import escape

from jsonschema import validate

default_colors = ['#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD', '#8C564B', '#E377C2', '#7F7F7F']

default_lines = ['-', '--', ':', '-.']

default_markers = ['o', 's', '^', 'p', 'v', "8"]


schema = {
    "type": "object",
    "properties": {
        "type": {"Description": "Reserved keyword. Must be \"plot\"", "type": "string"},
        "version": {"Description": "vfd file format version. Reserved for future use", "type": "string"},
        "xrange": {"Description": "Range of representation in the x-axis", "type": "array", "minItems": 2,
                   "maxItems": 2, "items": {"type": "number"}},
        "yrange": {"Description": "Range of representation in the y-axis", "type": "array", "minItems": 2,
                   "maxItems": 2, "items": {"type": "number"}},
        "xlabel": {"Description": "Label for the x-axis", "type": "string"},
        "ylabel": {"Description": "Label for the y-axis", "type": "string"},
        "legendtitle": {"Description": "A title to be placed in the legend", "type": "string"},
        "series": {"description": "Series of data in the plot", "type": "array", "minItems": 1, "items": {
            "type": "object", "properties": {
                "x": {"description": "x-coordinates of the points of the plot. Asummed integers from 1 if not given",
                      "type": "array",
                      "items": {"type": "number"},
                      },
                "y": {"description": "y-coordinates of the points of the plot",
                      "type": "array",
                      "items": {"type": "number"},
                      "minItems": 1, },
                "xerr": {"description": "Uncertainty in the x-axis of the points (in each direction)",
                         "type": "array",
                         "items": {"type": "number"},
                         },
                "yerr": {"description": "Uncertainty in the y-axis of the points (in each direction)",
                         "type": "array",
                         "items": {"type": "number"},
                         },
                "xmin": {"description": "Lower limit of the error bar in the x-axis. Has precedence over xerr",
                         "type": "array",
                         "items": {"type": "number"},
                         },
                "xmax": {"description": "Upper limit of the error bar in the x-axis. Has precedence over xerr",
                         "type": "array",
                         "items": {"type": "number"},
                         },
                "ymin": {"description": "Lower limit of the error bar in the y-axis. Has precedence over xerr",
                         "type": "array",
                         "items": {"type": "number"},
                         },
                "ymax": {"description": "Upper limit of the error bar in the y-axis. Has precedence over xerr",
                         "type": "array",
                         "items": {"type": "number"},
                         },
                "label": {"description": "Description of the series to be added to the legend if used",
                          "type": ["string", "number"]},
                "color": {"description": "An index representing the color used.",
                          "type": "integer"},
                "joined": {
                    "description": "Whether the data should be joined (representing a continuum) "
                                   "or not (representing the actual given points)",
                    "type": "boolean"}}}},
    },
    "required": ["series"]
}


def _cycle_property(index, property_list):
    return property_list[index % len(property_list)]


def _full_errorbar(values, error_limit, error, positive):
    """
    Get the argument needed for plt.errorbar error description.

    error_limit has precedence over error. If neither is specified, return a list of zeros.

    Args:
        values (list): Values of the variable.
        error_limit (list or float or None): Value(s) of the upper/lower limit.
        error (list or float or None): Value(s) of the uncertainty in the direction.
        positive (boolean): Whether it is a positive error.

    Returns:
        list of float: Uncertainty in the direction for all of the points.

    """
    if error_limit is not None:
        if isinstance(error_limit, list):
            if positive:
                return [y2 - y1 for y1, y2 in zip(values, error_limit)]
            else:
                return [y1 - y2 for y1, y2 in zip(values, error_limit)]
        else:
            if positive:
                return [y1 + error_limit for y1 in values]
            else:
                return [y1 - error_limit for y1 in values]
    elif error is not None:
        return error if isinstance(error, list) else [error] * len(values)

    else:
        return [0] * len(values)


def create_matplotlib_script(description, export_name="untitled", _indentation_size=4, context=None, export_format=None,
                             marker_list=None, color_list=None):
    """
    Create a matplotlib script to plot the VFD with the given description.

    Args:
        description (dict): Description of the VFD, obtained parsing the JSON.
        export_name (str): Name to give to the script file and the plots generated therein.
        _indentation_size (int): Size of the indentation used.
        context (str):  Matplotlib context to use in the script.
        export_format (str or list of str): Format(s) to export to.
        marker_list (list of str): Markers to use cyclically for series which are not joined.
        color_list (list): Colors to use when an index requests to do so.

    Returns:
        str: Python code which will create the plot.

    """
    # Markers will automatically switch always to distinguish the series.
    if marker_list is None:
        marker_list = default_markers
    # The other properties will do under explicit demand
    if color_list is None:
        color_list = default_colors

    code = "#!/usr/bin/env python\nimport matplotlib.pyplot as plt\n"
    indentation = ""
    if context is not None and context:
        if isinstance(context, str):
            code += "with plt.style.context('%s'):\n" % context
        else:
            code += "with plt.style.context(%s):\n" % context
        indentation = " " * _indentation_size

    if description["type"] == "plot":
        add_legend = False
        marker_count = 0  # Next index of a marker series
        for s in description["series"]:
            y = s["y"]
            if "x" in s:
                args = [s["x"], y]
            else:
                args = [y]
            kwargs = {}
            if "label" in s and s["label"]:
                kwargs["label"] = s["label"]
                add_legend = True
            if "color" in s:
                kwargs["color"] = _cycle_property(s["color"] - 1, color_list)  # User colors start at 1

            if any([i in s for i in {"xerr", "xmax", "xmin", "yerr", "ymin", "ymax"}]):
                # Error bar plot
                if "ymin" or "ymax" in s:
                    # Custom error bars
                    ymin = _full_errorbar(y, s["ymin"] if "ymin" in s else None, s["yerr"] if "yerr" in s else None,
                                          False)
                    ymax = _full_errorbar(y, s["ymax"] if "ymax" in s else None, s["yerr"] if "yerr" in s else None,
                                          True)

                    kwargs["yerr"] = [ymin, ymax]
                elif "yerr" in s:
                    kwargs["yerr"] = s["yerr"]
                if "xmin" or "xmax" in s:
                    # Custom error bars
                    x = s["x"] if "x" in s else list(range(len(y)))
                    xmin = _full_errorbar(x, s["xmin"] if "xmin" in s else None, s["xerr"] if "xerr" in s else None,
                                          False)
                    xmax = _full_errorbar(x, s["xmax"] if "xmax" in s else None, s["xerr"] if "xerr" in s else None,
                                          True)

                    kwargs["xerr"] = [xmin, xmax]
                elif "xerr" in s:
                    kwargs["xerr"] = s["xerr"]

                if "joined" in s:
                    if not s["joined"]:
                        kwargs["fmt"] = _cycle_property(marker_count, marker_list)
                        marker_count += 1

                # Add indentation to aid edition
                code += indentation + 'plt.errorbar(*%s,%s**%s)\n' % (args, "\n" + indentation + " " * 12, kwargs)
            else:
                # Regular plot
                if "joined" in s:
                    if not s["joined"]:
                        args.append(_cycle_property(marker_count, marker_list))
                        marker_count += 1
                if kwargs:
                    # Add indentation to aid edition
                    code += indentation + 'plt.plot(*%s,%s**%s)\n' % (args, "\n" + indentation + " " * 8, kwargs)
                else:
                    code += indentation + 'plt.plot(*%s)\n' % (args)

        if "xrange" in description:
            code += indentation + 'plt.xlim(%f,%f)\n' % (description["xrange"][0], description["xrange"][1])
        if "yrange" in description:
            code += indentation + 'plt.ylim(%f,%f)\n' % (description["yrange"][0], description["yrange"][1])

        if add_legend:
            if "legendtitle" in description:
                code += indentation + 'plt.legend(title="%s")\n' % escape(description["legendtitle"])
            else:
                code += indentation + 'plt.legend()\n'
        if "xlabel" in description:
            code += indentation + 'plt.xlabel("%s")\n' % escape(description["xlabel"])
        if "ylabel" in description:
            code += indentation + 'plt.ylabel("%s")\n' % escape(description["ylabel"])
        if export_format is None or not export_format:
            code += indentation + 'plt.gcf().canvas.set_window_title("%s")\n' % export_name
            code += indentation + 'plt.show()\n'
        else:
            if isinstance(export_format, str):
                export_format = [export_format]
            for f in export_format:
                code += indentation + 'plt.savefig("%s.%s")\n' % (export_name, f)
        return code
    else:
        raise ValueError("Unknown plot type: %s" % description["type"])


def create_scripts(path=".", run=False, blocking=True, expand_glob=True, **kwargs):
    """
    Create a script to generate a plot for the VFD file in the given path.

    Args:
        path (str): Path to the VFD file.
        run (bool): Whether to run the script upon creation.
        blocking (bool): If run is True, whether to wait for the calls to end.
        expand_glob (bool): Whether regular expressions are expanded (e.g., *.vfd or  **.vfd)
        **kwargs: Additional arguments to supply to `create_matplotlib_script`.

    Raises:
        FileNotFoundError: If the file was not found.
        json.JSONDecodeError: If the file was opened, but it is not a well-built JSON.
        jsonschema.ValidationError: If the opened file was a well-built JSON but not a well-built VFD.

    """
    if expand_glob:
        file_list = glob(path)
    else:
        file_list = [path]
    if not file_list:
        raise ValueError("No file matching " + path)
    for file in file_list:
        basename = os.path.basename(file)[:-4]
        pyfile_path = file[:-3] + "py"
        with open(pyfile_path, "w") as output:
            description = json.load(open(file))
            validate(description, schema)
            output.write(create_matplotlib_script(description, export_name=basename, **kwargs))
        if run:
            proc = subprocess.Popen(["python", os.path.abspath(pyfile_path)],
                                    cwd=os.path.abspath(os.path.dirname(pyfile_path)))
            if blocking:
                proc.wait()
