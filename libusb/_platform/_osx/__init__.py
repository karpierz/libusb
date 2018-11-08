# Copyright (c) 2016-2018, Adam Karpierz
# Licensed under the zlib/libpng License
# http://opensource.org/licenses/zlib

import sys
import os
import ctypes as ct

this_dir = os.path.dirname(os.path.abspath(__file__))
is_py32bit = sys.maxsize <= 2**32

DLL_PATH = os.path.join(this_dir, "x86" if is_py32bit else "x64", "libusb-1.0.dylib")

from ctypes  import CDLL      as DLL
from ctypes  import CFUNCTYPE as CFUNC
from _ctypes import dlclose

# Taken from the file sys/time.h.
#include <time.h>
#
# struct timeval {
#     time_t      tv_sec;   /* Seconds. */
#     suseconds_t tv_usec;  /* Microseconds. */
# };

class timeval(ct.Structure):
    _fields_ = [
    ("tv_sec",  time_t),       # seconds
    ("tv_usec", suseconds_t),  # microseconds
]
