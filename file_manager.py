#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import os

def open_folder(path):
    path = os.path.expanduser(path)

    if os.path.isfile(path):
        path = os.path.dirname(path)

    try:
        _platform_open(path)
    except Exception as e:
        print(e)


def _platform_open(path):
    if sys.platform.startswith('darwin'):
        subprocess.Popen(['open', path])
    elif sys.platform.startswith('linux'):
        subprocess.Popen(['xdg-open', path])
    elif sys.platform.startswith('win32'):
        subprocess.Popen(['explorer', path])
    else:
        print("unknown platform")

if __name__ == "__main__":
    open_folder("~")