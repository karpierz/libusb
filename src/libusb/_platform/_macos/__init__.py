# Copyright (c) 2016 Adam Karpierz
# SPDX-License-Identifier: Zlib

import sys
import os
import ctypes as ct

this_dir = os.path.dirname(os.path.abspath(__file__))
is_32bit = (sys.maxsize <= 2**32)
arch     = "x86" if is_32bit else "x64"
arch_dir = os.path.join(this_dir, arch)

def macos_version():
    import platform
    return tuple(int(x) for x in platform.mac_ver()[0].split("."))[:2]

if is_32bit:
    raise NotImplementedError("This OS is not supported in 32 bit!")

try:
    from ...__config__ import config
    DLL_PATH = config.get("LIBUSB", None)
    del config
    if DLL_PATH is None or DLL_PATH in ("", "None"):
        raise ImportError()
except ImportError:
    version = macos_version()
    if version < (10, 7):
        raise NotImplementedError("This OS version ({}) is not supported!"
                                  .format(".".join(str(x) for x in version)))
    ver_dir = "11.6" if version >= (11, 6) or version >= (10, 16) else "10.7"
    DLL_PATH = os.path.join(arch_dir, ver_dir, "libusb-1.0.0.dylib")

from ctypes  import CDLL as DLL         # noqa: E402
from _ctypes import dlclose             # noqa: E402
from ctypes  import CFUNCTYPE as CFUNC  # noqa: E402

# X32 kernel interface is 64-bit.
if False:  # if defined __x86_64__ && defined __ILP32__
    # quad_t is also 64 bits.
    time_t = suseconds_t = ct.c_longlong
else:
    time_t = suseconds_t = ct.c_long
# endif

# Taken from the file <sys/time.h>
# #include <time.h>
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
