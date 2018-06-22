# -*- coding: utf-8 -*-

"""Console script for vfd."""
import sys
import click

from . import vfd
from . import __version__


@click.command()
@click.argument('file', nargs=-1)
@click.option('--format', "-f", default='',
              help='Format of the output files. If none, an interactive window will open.')
@click.option('--style', "-s", default='',
              help='Matplotlib style(s) to use to generate the plot. Styles can be combined with commas (no spaces '
                   'among them). Styles further to the right overwrite values defined by styles to their left.')
@click.option('--tight', is_flag=True, help='Use tight_layout')
@click.option('--scalemulti', is_flag=True, help='Automatic scale of multiplots')
@click.option('--version', is_flag=True, help='Display version and exit')
def main(file, format, style, tight, scalemulti, version):
    """Command line interface for Vernacular Figure Description."""
    if version:
        click.echo("vfd " + __version__)
        exit(0)
    # NOTE: Styles with a comma in their names (!) won't be processed properly.
    # If we wanted to support this, a escape procedure should be defined.
    if style is not None and "," in style:
        style = style.split(",")
    xlsx = False
    if format is not None and "," in format:
        format = format.split(",")
        if "xlsx" in format:
            xlsx = True
            format.remove("xlsx")
    if format == "xlsx":
        xlsx = True
        format = None

    if file:
        for f in file:
            if xlsx:
                vfd.create_xlsx(path=f)
                if format:
                    vfd.create_scripts(path=f, export_format=format, context=style, run=True, tight_layout=tight,
                                       scale_multiplot=scalemulti)
            else:
                vfd.create_scripts(path=f, export_format=format, context=style, run=True, tight_layout=tight,
                                   scale_multiplot=scalemulti)
    else:
        _print_help_msg(main)
    return 0


def _print_help_msg(command):
    with click.Context(command) as ctx:
        click.echo(command.get_help(ctx))


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
