#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the builder module."""
import math

import numpy as np

from vfd import builder


def test_ensure_normal_type():
    """Test numpy types and NaNs are removed"""
    assert ([1, 2],) == builder._ensure_normal_type(np.arange(1, 3))
    assert type(builder._ensure_normal_type(np.arange(1, 3))[0]) == list
    assert ([1, 2],) == builder._ensure_normal_type([1, np.nan, 2])
    assert ([1, 2],) == builder._ensure_normal_type([1, math.nan, 2])
    assert ([1, 2], [3, 4]) == builder._ensure_normal_type([1, 2], [3, 4])
    assert ([1, 2], [10, 20]) == builder._ensure_normal_type([1, np.nan, 2], [10, 13, 20])
