# Copyright (c) 2016-2019, Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/licenses/zlib/

import sys
import os
import ctypes as ct

this_dir = os.path.dirname(os.path.abspath(__file__))
is_32bit = (sys.maxsize <= 2**32)

arch = "x86" if is_32bit else "x64"
DLL_PATH = os.path.join(this_dir, arch, "libusb-1.0.dylib")

from ctypes  import CDLL      as DLL
from ctypes  import CFUNCTYPE as CFUNC
from _ctypes import dlclose

# Taken from the file <sys/time.h>
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
