#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the builder module."""
import math

import numpy as np

from vfd import builder


def test_ensure_normal_type():
    """Test numpy types and NaNs are removed"""
    # Numpy arrays
    assert ([1, 2],) == builder._ensure_normal_type(np.arange(1, 3))
    assert type(builder._ensure_normal_type(np.arange(1, 3))[0]) == list

    # Numpy special types in regular list
    assert ([1, 2],) == builder._ensure_normal_type([1, np.nan, 2])
    assert ([1, 2],) == builder._ensure_normal_type([1, np.inf, 2])

    # Non finite Python types
    try:
        nan_list = [1, math.nan, 2]
        assert ([1, 2],) == builder._ensure_normal_type(nan_list)
    except AttributeError:  # Old python with no nan in math
        pass

    try:
        inf_list = [1, math.inf, 2]
        assert ([1, 2],) == builder._ensure_normal_type(inf_list)
    except AttributeError:  # Old python with no nan in math
        pass

    # Two lists
    assert ([1, 2], [3, 4]) == builder._ensure_normal_type([1, 2], [3, 4])
    assert ([1, 2], [10, 20]) == builder._ensure_normal_type([1, np.nan, 2], [10, 13, 20])
