# -*- coding: utf-8 -*-

"""Console script for vfd."""
import sys
import click

from . import vfd


@click.command()
@click.argument('file', nargs=-1)
@click.option('--format', default='', help='Format of the output files. If none, an interactive window will open.')
@click.option('--style', default='', help='Matplotlib style(s) to use to generate the plot. Styles can be combined '
                                          'with a / (no spaces among them). Styles further to the right overwrite '
                                          'values defined by styles to their left.')
def main(file, format, style):
    """Command line interface for Vernacular Figure Description."""
    if style is not None and "/" in style:
        style = style.split("/")
    if file:
        for f in file:
            vfd.create_scripts(path=f, export_format=format, context=style, run=True)
    else:
        _print_help_msg(main)
    return 0


def _print_help_msg(command):
    with click.Context(command) as ctx:
        click.echo(command.get_help(ctx))


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
