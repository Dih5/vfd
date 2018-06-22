#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the builder module."""
import os
import shutil
import filecmp

import numpy as np

from vfd import builder, vfd


def test_ensure_normal_type():
    """Test numpy types and NaNs are removed"""
    # Numpy arrays
    assert ([1, 2],) == builder._ensure_normal_type(np.arange(1, 3))
    assert type(builder._ensure_normal_type(np.arange(1, 3))[0]) == list

    # Numpy special types in regular list
    assert ([1, 2],) == builder._ensure_normal_type([1, np.nan, 2])
    assert ([1, 2],) == builder._ensure_normal_type([1, np.inf, 2])

    # Non finite Python types
    assert ([1, 2],) == builder._ensure_normal_type([1, float('nan'), 2])
    assert ([1, 2],) == builder._ensure_normal_type([1, float('inf'), 2])

    # Two lists
    assert ([1, 2], [3, 4]) == builder._ensure_normal_type([1, 2], [3, 4])
    assert ([1, 2], [10, 20]) == builder._ensure_normal_type([1, np.nan, 2], [10, 13, 20])


def test_builder_runs(tmpdir):
    """Test the Builder class is working"""
    export_format = 'png'

    # Set paths
    temp_path = str(tmpdir)  # Conversion needed in python < 3.6 to work with os.path
    temp_vfd = os.path.join(temp_path, "builder.vfd")
    temp_plt = os.path.join(temp_path, "builder." + export_format)

    with builder.Builder() as p:
        p.plot([1, 2, 3], label="Data")
        p.xlabel("Test")
        p.title("A test")
        p.legend()
        p.savefig(temp_plt)
    # Copy the original file
    shutil.copyfile(temp_plt, temp_plt + ".orig")
    # Run the VFD
    vfd.create_scripts(temp_vfd, run=True, blocking=True, export_format=export_format)
    # Compare the files
    assert filecmp.cmp(temp_plt, temp_plt + ".orig")


def test_errobar():
    p = builder.Builder()
    p.errorbar([1, 2, 3], [1, 4, 9], yerr=1)
    assert p.data["series"][-1]["yerr"] == [1, 1, 1]
    p.errorbar([1, 2, 3], [1, 4, 9], yerr=[1, 1.5, 3])
    assert p.data["series"][-1]["yerr"] == [1, 1.5, 3]
    p.errorbar([1, 2, 3], [1, 4, 9], yerr=[[0.1, 0.2, 0.3], [0.2, 0.3, 0.4]])
    assert p.data["series"][-1]["ymax"] == [1.1, 4.2, 9.3]
    assert p.data["series"][-1]["ymin"] == [0.8, 3.7, 8.6]


def test_colorplot():
    """Test colorplot are generated"""
    z = [[1, 2, 3], [4, 5, 6]]
    for f in ["contour", "contourf", "pcolor", "pcolormesh"]:
        p = builder.Builder()
        getattr(p, f)(z)
        assert p.data["type"] == "colorplot"
        assert p.data["z"] == z

    x = [5, 6, 7]
    y = [10, 11]

    for f in ["contour", "contourf", "pcolor", "pcolormesh"]:
        p = builder.Builder()
        getattr(p, f)(x, y, z)
        assert p.data["type"] == "colorplot"
        assert p.data["x"] == x
        assert p.data["y"] == y
        assert p.data["z"] == z

    # Test with pcolor meshes with N+1 points
    x = [5, 6, 7, 8]
    y = [10, 11, 12]

    for f in ["pcolor", "pcolormesh"]:
        p = builder.Builder()
        getattr(p, f)(x, y, z)
        assert p.data["type"] == "colorplot"
        assert p.data["x"] == [5.5, 6.5, 7.5]
        assert p.data["y"] == [10.5, 11.5]
        assert p.data["z"] == z


def test_multiplot():
    """Test multiplot functionality"""
    # Just check subplot properties are retrieved by the main instance
    p = builder.Builder()
    fig, axes = p.subplots(1, 1)
    axes.plot([1, 2, 3])
    data = p.get_data()
    assert data["plots"][0][0]["series"][0]["y"] == [1, 2, 3]

    p = builder.Builder()
    fig, axes = p.subplots(2, 1)  # 2 rows, 1 col
    axes[0].plot([1, 2, 3])
    axes[1].plot([2, 3, 4])
    data = p.get_data()
    assert data["plots"][0][0]["series"][0]["y"] == [1, 2, 3]
    assert data["plots"][1][0]["series"][0]["y"] == [2, 3, 4]

    p = builder.Builder()
    fig, axes = p.subplots(2, 1, squeeze=False)  # 2 rows, 1 col
    axes[0][0].plot([1, 2, 3])
    axes[1][0].plot([2, 3, 4])
    data = p.get_data()
    assert data["plots"][0][0]["series"][0]["y"] == [1, 2, 3]
    assert data["plots"][1][0]["series"][0]["y"] == [2, 3, 4]

    p = builder.Builder()
    fig, axes = p.subplots(2, 2, sharex=True)  # 2 rows, 2 col
    axes[0][0].plot([1, 2, 3])
    axes[1][0].plot([2, 3, 4])
    axes[0][1].plot([3, 4, 5])
    axes[1][1].plot([4, 5, 6])
    data = p.get_data()
    assert data["plots"][0][0]["series"][0]["y"] == [1, 2, 3]
    assert data["plots"][1][0]["series"][0]["y"] == [2, 3, 4]
    assert data["plots"][0][1]["series"][0]["y"] == [3, 4, 5]
    assert data["plots"][1][1]["series"][0]["y"] == [4, 5, 6]
    assert data["xshared"] == "all"


def test_twinx():
    """Test twinx functionality"""
    # Just check subplot properties are retrieved by the main instance
    p = builder.Builder()
    fig, ax = p.subplots()
    twinx = ax.twinx()
    ax.plot([1.0, 2.0, 3.0], [1.0, 2.0, 9.0])
    twinx.semilogy([1.0, 2.0, 3.0], [1.0, 1.5, 1.0])
    ax.set_ylabel("Romulus")
    twinx.set_ylabel("Remus")
    twinx.set_ylim(0.1, 2.1)

    data = p.get_data()["plots"][0][0]

    assert "xadded" not in data["series"][0]
    assert "yadded" not in data["series"][0]
    assert "xadded" not in data["series"][1]
    assert "yadded" in data["series"][1]
    assert data["ylabel"] == "Romulus"
    assert data["yadded"][0]["label"] == "Remus"
    assert data["yadded"][0]["range"] == (0.1, 2.1)


def test_twiny():
    """Test twiny functionality"""
    # Just check subplot properties are retrieved by the main instance
    p = builder.Builder()
    fig, ax = p.subplots()
    twiny = ax.twiny()
    ax.plot([1.0, 2.0, 3.0], [1.0, 2.0, 9.0])
    twiny.semilogx([1.0, 2.0, 3.0], [1.0, 1.5, 1.0])
    ax.set_xlabel("Romulus")
    twiny.set_xlabel("Remus")
    twiny.set_xlim(0.1, 2.1)

    data = p.get_data()["plots"][0][0]

    assert "xadded" not in data["series"][0]
    assert "yadded" not in data["series"][0]
    assert "xadded" in data["series"][1]
    assert "yadded" not in data["series"][1]
    assert data["xlabel"] == "Romulus"
    assert data["xadded"][0]["label"] == "Remus"
    assert data["xadded"][0]["range"] == (0.1, 2.1)
