#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `vfd` package."""

import os
import shutil
import tempfile
import subprocess
import filecmp
from glob import glob

from click.testing import CliRunner

from vfd import cli
from vfd import vfd

try:
    from tempfile import TemporaryDirectory
except ImportError:
    class TemporaryDirectory(object):
        """Py2-compatible tempfile.TemporaryDirectory"""

        def __enter__(self):
            self.dir_name = tempfile.mkdtemp()
            return self.dir_name

        def __exit__(self, exc_type, exc_value, traceback):
            shutil.rmtree(self.dir_name)


def test_command_line_interface():
    """Test the CLI runs"""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0

    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert 'Show this message and exit.' in help_result.output


def test_errobar():
    """Test the error bar logic"""
    assert vfd._full_errorbar([1, 2, 3], [2, 3, 4], None, True) == [1, 1, 1]
    assert vfd._full_errorbar([1, 2, 3], [0, 1, 2], None, False) == [1, 1, 1]
    assert vfd._full_errorbar([1, 2, 3], None, 2, True) == [2, 2, 2]
    assert vfd._full_errorbar([1, 2, 3], None, [2, 2, 2], False) == [2, 2, 2]
    assert vfd._full_errorbar([1, 2, 3], [2, 3, 4], 2, True) == [1, 1, 1]


def test_plot_files():
    """Test the plotting is working"""
    export_format = 'png'
    with TemporaryDirectory() as temp:
        try:
            os.makedirs(temp)
        except OSError:
            # Either already existing or unable to create it
            pass
        for file in glob(os.path.join("tests", "plot-tests", "*.vfd")):
            # Copy the .vfd
            name = os.path.basename(file)
            temp_vfd = os.path.join(temp, name[:-3] + "test.vfd")
            shutil.copyfile(file, temp_vfd)
            # Run it
            vfd.create_scripts(temp_vfd, run=True, blocking=True, export_format=export_format)
            # Copy the reference script
            temp_ref = os.path.join(temp, name[:-3] + "py")
            shutil.copyfile(file[:-3] + "py", temp_ref)
            # Run it
            proc = subprocess.Popen(["python", os.path.abspath(temp_ref)], cwd=os.path.abspath(temp))
            proc.wait()
            # Compare the files
            assert filecmp.cmp(temp_vfd[:-3] + export_format, temp_ref[:-2] + export_format)
