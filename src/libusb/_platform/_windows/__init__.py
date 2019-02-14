# Copyright (c) 2016-2018, Adam Karpierz
# Licensed under the zlib/libpng License
# http://opensource.org/licenses/zlib

import sys
import os
import ctypes as ct

this_dir = os.path.dirname(os.path.abspath(__file__))
is_py32bit = sys.maxsize <= 2**32

arch = "x86" if is_py32bit else "x64"
DLL_PATH = os.path.join(this_dir, arch, "libusb-1.0.dll")

from ctypes  import WinDLL      as DLL
from ctypes  import WINFUNCTYPE as CFUNC
from _ctypes import FreeLibrary as dlclose

# Taken from the file winsock.h.
#
# struct timeval {
#     long tv_sec;   /* seconds */
#     long tv_usec;  /* and microseconds */
# };

class timeval(ct.Structure):
    _fields_ = [
    ("tv_sec",  ct.c_long),  # seconds
    ("tv_usec", ct.c_long),  # microseconds
]
