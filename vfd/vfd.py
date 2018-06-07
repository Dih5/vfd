# -*- coding: utf-8 -*-

"""Python API for vfd"""
import json
from glob import glob
import os
import subprocess

from jsonschema import validate as validate_schema

default_colors = ['#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD', '#8C564B', '#E377C2', '#7F7F7F']

default_lines = ['-', '--', ':', '-.']

default_markers = ['o', 's', '^', 'p', 'v', "8"]

_indentation_size = 4

schema_style = {
    "type": "object",
    "properties": {
        "lines": {"Description": "List of lines suggested for each index of the plot", "type": "array",
                  "items": {"type": "string"}},
        "colors": {"Description": "List of colors suggested for each index of the plot", "type": "array",
                   "items": {"type": "string"}},
        "markers": {"Description": "List of markers suggested for each index of the plot", "type": "array",
                    "items": {"type": "string"}}
    }
}

schema_plot = {
    "type": "object",
    "properties": {
        "type": {"Description": "Reserved keyword. Must be \"plot\"", "type": "string"},
        "version": {"Description": "vfd file format version. Reserved for future use", "type": "string"},
        "xrange": {"Description": "Range of representation in the x-axis", "type": "array", "minItems": 2,
                   "maxItems": 2, "items": {"type": "number"}},
        "yrange": {"Description": "Range of representation in the y-axis", "type": "array", "minItems": 2,
                   "maxItems": 2, "items": {"type": "number"}},
        "xlog": {"Description": "Whether the scale should be logarithmic in the x-axis", "type": "boolean"},
        "ylog": {"Description": "Whether the scale should be logarithmic in the y-axis", "type": "boolean"},
        "xlabel": {"Description": "Label for the x-axis", "type": "string"},
        "ylabel": {"Description": "Label for the y-axis", "type": "string"},
        "title": {"Description": "Title for the plot", "type": "string"},
        "legendtitle": {"Description": "A title to be placed in the legend", "type": "string"},
        "series": {"description": "Series of data in the plot", "type": "array", "minItems": 1, "items": {
            "type": "object", "properties": {
                "x": {"description": "x-coordinates of the points of the plot. Assumed integers from 1 if not given",
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
                "line": {"description": "An index representing the line style used. 1 should be a solid line.",
                         "type": "integer"},
                "joined": {
                    "description": "Whether the data should be joined (representing a continuum) "
                                   "or not (representing the actual given points)",
                    "type": "boolean"}}}},

        "style": schema_style,
    },
    "required": ["series"]
}

schema_colorplot = {
    "type": "object",
    "properties": {
        "type": {"Description": "Reserved keyword. Must be \"colorplot\"", "type": "string"},
        "version": {"Description": "vfd file format version. Reserved for future use", "type": "string"},
        "xrange": {"Description": "Range of representation in the x-axis", "type": "array", "minItems": 2,
                   "maxItems": 2, "items": {"type": "number"}},
        "yrange": {"Description": "Range of representation in the y-axis", "type": "array", "minItems": 2,
                   "maxItems": 2, "items": {"type": "number"}},
        "xlog": {"Description": "Whether the scale should be logarithmic in the x-axis", "type": "boolean"},
        "ylog": {"Description": "Whether the scale should be logarithmic in the y-axis", "type": "boolean"},
        "zlog": {"Description": "Whether the color scale should be logarithmic", "type": "boolean"},
        "xlabel": {"Description": "Label for the x-axis", "type": "string"},
        "ylabel": {"Description": "Label for the y-axis", "type": "string"},
        "contour": {"Description": "Whether contour should be plotted instead of density", "type": "boolean"},
        "fillcontour": {"Description": "When contour is plotted, whether regions should be filled", "type": "boolean"},
        "title": {"Description": "Title for the plot", "type": "string"},
        "x": {"description": "x-coordinates of the mesh of the plot. Assumed integers from 1 if not given",
              "type": "array",
              "items": {"type": "number"},
              },
        "y": {"description": "y-coordinates of the mesh of the plot. Assumed integers from 1 if not given",
              "type": "array",
              "items": {"type": "number"},
              },
        "z": {"description": "Matrix of values to plot",
              "type": "array",
              "items": {"type": "array", "items": {"type": "number"}},
              },

        "style": schema_style,
    },
    "required": ["z"]
}

schema_multiplot = {
    "type": "object",
    "properties": {
        "type": {"Description": "Reserved keyword. Must be \"multiplot\"", "type": "string"},
        "version": {"Description": "vfd file format version. Reserved for future use", "type": "string"},
        "plots": {
            "Description": "Bidimensional matrix of plots. Each item of this array is an array with a row of plots",
            "type": "array",
            "items": {"type": "array", "items": {"anyof": [schema_plot, schema_colorplot]}}},
        "title": {"Description": "Title for the plots", "type": "string"},
        "xshared": {"Description:": "If x-axis should be shared", "type": "string", "pattern": "^(all|none|row|col)$"},
        "yshared": {"Description:": "If y-axis should be shared", "type": "string", "pattern": "^(all|none|row|col)$"},
        "joined": {"Description:": "If the subplots should be adjacent in horizontal and vertical respectively",
                   "type": "array", "minitems": 2, "maxitems": 2, "items": {"type": "boolean"}},
        "style": schema_style
    },
    "required": ["plots"]
}


# TODO: Add epilog to schemas


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


def _to_code_string(string):
    """
    Transform a string into a suitable representation of print code.

    E.g. in printed form: O'Hara -> r'O\'Hara'

    """
    if '"' not in string:
        return 'r"' + string + '"'
    elif "'" not in string:
        return "r'" + string + "'"
    else:
        # Double the original backslash first, then escape the ""
        return '"' + string.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _get_style(description):
    """
    Get the kwargs from a style_schema

    Args:
        description (dict): A style_schema.

    Returns:
        dict: A dictionary with the kwargs.

    """
    kwargs = {}
    if "lines" in description:
        kwargs["line_style"] = description["lines"]
    if "colors" in description:
        kwargs["color_list"] = description["colors"]
    if "markers" in description:
        kwargs["marker_list"] = description["markers"]
    return kwargs


def _create_matplotlib_plot(description, container="plt", current_axes=True, indentation_level=0, marker_list=None,
                            color_list=None, line_list=None, title_inside=False):
    """
    Create code describing a simple plot.

    Args:
        description (dict): A part of VFD of type "plot", parsed from the JSON.
        container (str): The object whose methods are called. E.g., 'plt' for pyplot or an axes.
        current_axes (bool): Whether to call the set_* methods of the container or the current axes methods (for 'plt').
        indentation_level: Indentation level for the code.
        marker_list (list of str): Markers to use cyclically for series which are not joined.
        color_list (list): Colors to use when an index requests to do so.
        line_list (list of str): Line styles to use when requested.
        title_inside (bool): Insert the title as text inside the plot instead as a title. Useful for multiplots.

    Returns:
        str: Python code which will create the plot.

    """
    # Markers will automatically switch always to distinguish the series.
    if marker_list is None:
        marker_list = default_markers
    # The other properties will do under explicit demand (otherwise it's left to matplotlib's style)
    if color_list is None:
        color_list = default_colors
        explicit_colors = False
    else:
        explicit_colors = True
    if line_list is None:
        line_list = default_lines
        explicit_lines = False
    else:
        explicit_lines = True
    add_legend = False
    # Counters for automatic properties:
    marker_count = 0
    color_count = 0
    line_count = 0
    code = ""
    indentation = " " * (indentation_level * _indentation_size)
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
        elif explicit_colors:
            kwargs["color"] = _cycle_property(color_count, color_list)
            color_count += 1
        if "line" in s:
            kwargs["linestyle"] = _cycle_property(s["line"] - 1, line_list)
        elif explicit_lines:
            kwargs["linestyle"] = _cycle_property(line_count, line_list)
            line_count += 1

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
            code += indentation + container + '.errorbar(*%s,%s**%s)\n' % (args, "\n" + indentation + " " * 12, kwargs)
        else:
            # Regular plot
            if "joined" in s:
                if not s["joined"]:
                    args.append(_cycle_property(marker_count, marker_list))
                    marker_count += 1
            if kwargs:
                # Add indentation to aid edition
                code += indentation + container + '.plot(*%s,%s**%s)\n' % (args, "\n" + indentation + " " * 8, kwargs)
            else:
                code += indentation + container + '.plot(*%s)\n' % (args)

    if "xrange" in description:
        code += indentation + container + ('.' if current_axes else '.set_') + 'xlim(%f,%f)\n' % (
            description["xrange"][0], description["xrange"][1])
    if "yrange" in description:
        code += indentation + container + ('.' if current_axes else '.set_') + 'ylim(%f,%f)\n' % (
            description["yrange"][0], description["yrange"][1])

    if "xlog" in description and description["xlog"]:
        code += indentation + container + ('.' if current_axes else '.set_') + 'xscale("log")\n'
    if "ylog" in description and description["ylog"]:
        code += indentation + container + ('.' if current_axes else '.set_') + 'yscale("log")\n'

    if add_legend:
        if "legendtitle" in description:
            code += indentation + container + '.legend(title=%s)\n' % _to_code_string(description["legendtitle"])
        else:
            code += indentation + container + '.legend()\n'
    if "xlabel" in description:
        code += indentation + container + ('.' if current_axes else '.set_') + 'xlabel(%s)\n' % _to_code_string(
            description["xlabel"])
    if "ylabel" in description:
        code += indentation + container + ('.' if current_axes else '.set_') + 'ylabel(%s)\n' % _to_code_string(
            description["ylabel"])
    if "title" in description and description["title"]:
        # Title can be requested to go inside the figure as a text.
        # This is useful for multiplots, where an upper title can be confusing.
        if title_inside:
            code += indentation + container + '.text(.5,.95,%s, horizontalalignment="center",' \
                                              'transform=%s.transAxes)\n' % (_to_code_string(description["title"]),
                                                                             container)
        else:
            code += indentation + container + ('.' if current_axes else '.set_') + 'title(%s)\n' % _to_code_string(
                description["title"])
    if "epilog" in description:
        for directive in description["epilog"]:
            if directive["type"] == "text":
                code += indentation + container + ".text(%f, %f, %s)\n" % (
                    directive["x"], directive["y"], _to_code_string(directive["text"]))
                pass
            else:
                raise ValueError("Unknown epilog directive: " + directive["type"])
    return code


def _create_matplotlib_colorplot(description, container="plt", current_axes=True, indentation_level=0, rasterized=True):
    """
    Create code describing a simple plot.

    Args:
        description (dict): A part of VFD of type "colorplot", parsed from the JSON.
        container (str): The object whose methods are called. E.g., 'plt' for pyplot or an axes.
        current_axes (bool): Whether to call the set_* methods of the container or the current axes methods (for 'plt').
        indentation_level: Indentation level for the code.
        rasterized (bool): Whether the plot should be rasterized

    Returns:
        str: Python code which will create the plot.

    """
    code = ""
    indentation = " " * (indentation_level * _indentation_size)
    plot_f = "pcolormesh"
    if "contour" in description:
        if description["contour"]:
            plot_f = "contour"
            try:
                if description["fillcontour"]:
                    plot_f = "contourf"
            except KeyError:
                pass

    try:
        if description["zlog"]:
            code += indentation + "from matplotlib.colors import LogNorm\n"
    except KeyError:
        pass

    # Store the ContourSet to label or rasterize it later
    code += indentation
    if plot_f in ["contour", "contourf"]:
        code += "cs = "

    # Leave call open for other args
    if "x" and "y" in description:
        code += container + '.%s(%s,%s,%s' % (plot_f, description["x"], description["y"], description["z"])
    else:
        code += container + '.%s(%s' % (plot_f, description["z"])

    try:
        if description["zlog"]:
            code += ", norm=LogNorm()"
    except KeyError:
        pass

    if rasterized and plot_f == "pcolormesh":
        code += ", rasterized=True"

    code += ')\n'

    if rasterized and plot_f in ["contour", "contourf"]:
        code += indentation + "for c in cs.collections:\n" + indentation + " " * _indentation_size + \
                "c.set_rasterized(True)\n"

    try:
        if description["xlog"]:
            code += indentation + 'plt.gca().set_xscale("log")\n'
    except KeyError:
        pass

    try:
        if description["ylog"]:
            code += indentation + 'plt.gca().set_yscale("log")\n'
    except KeyError:
        pass

    if "xlabel" in description:
        code += indentation + container + ('.' if current_axes else '.set_') + 'xlabel(%s)\n' % _to_code_string(
            description["xlabel"])
    if "ylabel" in description:
        code += indentation + container + ('.' if current_axes else '.set_') + 'ylabel(%s)\n' % _to_code_string(
            description["ylabel"])
    if "title" in description and description["title"]:
        code += indentation + container + ('.' if current_axes else '.set_') + 'title(%s)\n' % _to_code_string(
            description["title"])

    # If contour lines, label them. Otherwise, add the colorbar.
    if plot_f == "contour":
        code += indentation + "plt.clabel(cs)\n"
    else:
        code += indentation + "plt.colorbar()\n"
    return code


def create_matplotlib_script(description, export_name="untitled", context=None, export_format=None,
                             marker_list=None, color_list=None, line_list=None, tight_layout=None,
                             scale_multiplot=False):
    """
    Create a matplotlib script to plot the VFD with the given description.

    Args:
        description (dict): Description of the VFD, obtained parsing the JSON.
        export_name (str): Name to give to the script file and the plots generated therein.
        context (str):  Matplotlib context to use in the script.
        export_format (str or list of str): Format(s) to export to.
        marker_list (list of str): Markers to use cyclically for series which are not joined.
        color_list (list): Colors to use when an index requests to do so.
        line_list (list of str): Line styles to use when requested.
        tight_layout (bool): Use the tight_layout function to fit the plot.
        scale_multiplot (bool): Whether to automatically increase the size of multiplots.

    Returns:
        str: Python code which will create the plot.

    """
    # Consider only top level style hinting
    if "style" in description:
        style_description = description["style"]
        if line_list is None and "lines" in style_description:
            line_list = style_description["lines"]
        if color_list is None and "colors" in style_description:
            color_list = style_description["colors"]
        if marker_list is None and "markers" in style_description:
            marker_list = style_description["markers"]

    code = "#!/usr/bin/env python\nimport matplotlib.pyplot as plt\n"
    indentation = ""
    indentation_level = 0
    if context is not None and context:
        if isinstance(context, str):
            code += "with plt.style.context(%s):\n" % _to_code_string(context)
        elif isinstance(context, list):
            code += "with plt.style.context([%s]):\n" % ", ".join([_to_code_string(s) for s in context])
        else:
            raise TypeError("context must be a str or a list of str")
        indentation_level = 1
        indentation = " " * _indentation_size

    if description["type"] == "plot":
        code += _create_matplotlib_plot(description, indentation_level=indentation_level, marker_list=marker_list,
                                        color_list=color_list, line_list=line_list, )
        if tight_layout:
            code += indentation + "plt.tight_layout()\n"

    elif description["type"] == "multiplot":
        plots_ver = len(description["plots"])
        plots_hor = len(description["plots"][0])
        if scale_multiplot:
            code += indentation + "size_x, size_y= plt.rcParams.get('figure.figsize')\n"
        code += indentation + "fig, axarr = plt.subplots(%d, %d" % (plots_ver, plots_hor)  # Note unfinished line
        if "xshared" in description:
            code += ', sharex="%s"' % description["xshared"]
        if "yshared" in description:
            code += ', sharey="%s"' % description["yshared"]
        if scale_multiplot:
            code += ", figsize=(%d * size_x, %d * size_y)" % (plots_hor, plots_ver)
        code += ")\n"

        # TODO: Add colorplot support

        if plots_hor == 1 and plots_ver == 1:
            code += _create_matplotlib_plot(description["plots"][0][0], container="axarr", current_axes=False,
                                            indentation_level=indentation_level, marker_list=marker_list,
                                            color_list=color_list, line_list=line_list, title_inside=True)
        elif plots_hor == 1:
            for i in range(plots_ver):
                code += _create_matplotlib_plot(description["plots"][i][0], container="axarr[%d]" % i,
                                                current_axes=False, indentation_level=indentation_level,
                                                marker_list=marker_list, color_list=color_list,
                                                line_list=line_list, title_inside=True)
        elif plots_ver == 1:
            for j in range(plots_hor):
                code += _create_matplotlib_plot(description["plots"][0][j], container="axarr[%d]" % j,
                                                current_axes=False, indentation_level=indentation_level,
                                                marker_list=marker_list, color_list=color_list,
                                                line_list=line_list, title_inside=True)
        else:
            for i in range(plots_ver):
                for j in range(plots_hor):
                    code += _create_matplotlib_plot(description["plots"][i][j], container="axarr[%d][%d]" % (i, j),
                                                    current_axes=False, indentation_level=indentation_level,
                                                    marker_list=marker_list, color_list=color_list,
                                                    line_list=line_list, title_inside=True)
        if "title" in description:
            code += indentation + 'fig.suptitle(%s)\n' % _to_code_string(description["title"])

        if tight_layout:
            code += indentation + "plt.tight_layout()\n"
        # Always join after the tight_layout to avoid splitting.
        try:
            joined = description["joined"]
            if joined[1]:  # Vertical-joined
                code += indentation + "fig.subplots_adjust(hspace=0)\n"
            if joined[0]:  # Horizontal-joined
                code += indentation + "fig.subplots_adjust(wspace=0)\n"
        except KeyError:
            pass

    elif description["type"] == "colorplot":
        code += _create_matplotlib_colorplot(description, indentation_level=indentation_level)
        if tight_layout:
            code += indentation + "plt.tight_layout()\n"

    else:
        raise ValueError("Unknown plot type: %s" % description["type"])

    if export_format is None or not export_format:
        code += indentation + 'plt.gcf().canvas.set_window_title(%s)\n' % _to_code_string(export_name)
        code += indentation + 'plt.show()\n'
    else:
        if isinstance(export_format, str):
            export_format = [export_format]
        for f in export_format:
            code += indentation + 'plt.savefig("%s.%s")\n' % (export_name, f)
    return code


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
            if "type" not in description:
                raise ValueError("No type in provided file")
            if description["type"] == "plot":
                validate_schema(description, schema_plot)
            elif description["type"] == "multiplot":
                validate_schema(description, schema_multiplot)
            elif description["type"] == "colorplot":
                validate_schema(description, schema_colorplot)
            else:
                raise ValueError("Unknown type: %s" % description["type"])

            # If it's a single item multiplot, skip the multiplot container
            if description["type"] == "multiplot" and len(description["plots"]) == 1 and len(
                description["plots"][0]) == 1:
                output.write(create_matplotlib_script(description["plots"][0][0], export_name=basename, **kwargs))
            else:
                output.write(create_matplotlib_script(description, export_name=basename, **kwargs))
        if run:
            proc = subprocess.Popen(["python", os.path.abspath(pyfile_path)],
                                    cwd=os.path.abspath(os.path.dirname(pyfile_path)))
            if blocking:
                proc.wait()
