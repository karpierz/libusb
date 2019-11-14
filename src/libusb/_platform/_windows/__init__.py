# Copyright (c) 2016-2019 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/licenses/zlib/

import sys
import os
import ctypes as ct

this_dir = os.path.dirname(os.path.abspath(__file__))
is_32bit = (sys.maxsize <= 2**32)

arch = "x86" if is_32bit else "x64"
DLL_PATH = os.path.join(this_dir, arch, "libusb-1.0.dll")

from ctypes  import WinDLL      as DLL
from ctypes  import WINFUNCTYPE as CFUNC
from _ctypes import FreeLibrary as dlclose

# Winsock doesn't have this POSIX type; it's used for the
# tv_usec value of struct timeval.
suseconds_t = ct.c_long

# Taken from the file <winsock.h>
#
# struct timeval {
#     long tv_sec;   /* seconds */
#     long tv_usec;  /* and microseconds */
# };

class timeval(ct.Structure):
    _fields_ = [
    ("tv_sec",  ct.c_long),    # seconds
    ("tv_usec", suseconds_t),  # microseconds
]
