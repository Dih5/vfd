#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `vfd` package."""

import os
import shutil
import subprocess
import filecmp
from glob import glob

from click.testing import CliRunner
import pytest

from vfd import cli
from vfd import vfd


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


@pytest.fixture
def get_plot_test_list():
    return glob(os.path.join("tests", "plot-tests", "*.vfd"))


@pytest.mark.parametrize('file', get_plot_test_list())
def test_plot_files(tmpdir, file):
    """Test the plotting is working"""
    export_format = 'png'

    # Copy the .vfd
    name = os.path.basename(file)
    temp_path = str(tmpdir)  # Conversion needed in python < 3.6 to work with os.path
    temp_vfd = os.path.join(temp_path, name[:-3] + "test.vfd")
    shutil.copyfile(file, temp_vfd)
    # Run it
    vfd.create_scripts(temp_vfd, run=True, blocking=True, export_format=export_format)
    # Copy the reference script
    temp_ref = os.path.join(temp_path, name[:-3] + "py")
    shutil.copyfile(file[:-3] + "py", temp_ref)
    # Run it
    proc = subprocess.Popen(["python", os.path.abspath(temp_ref)], cwd=os.path.abspath(temp_path))
    proc.wait()
    # Compare the files
    assert filecmp.cmp(temp_vfd[:-3] + export_format, temp_ref[:-2] + export_format)
