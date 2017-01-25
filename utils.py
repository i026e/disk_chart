#!/usr/bin/env python3
# -*- coding: utf-8 -*-

SIZE_NAMES = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
SIZE_FMT = "{size:.1f} {units}"

def in_range(val, min_, max_):
    return max(min_, min(max_, val))

def pretty_size(size):
    max_unit = len(SIZE_NAMES) - 1

    unit = 0
    while (size > 1024) and (unit < max_unit):
        size /= 1024.0
        unit += 1

    return SIZE_FMT.format(size = size, units = SIZE_NAMES[unit])