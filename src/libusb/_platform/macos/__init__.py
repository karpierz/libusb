# Copyright (c) 2016 Adam Karpierz
# SPDX-License-Identifier: Zlib

import platform
from pathlib import Path

from utlx import module_path
from utlx.platform import arch
from utlx.platform.capi import DLL, dlclose, CFUNC
from utlx.platform.macos import macos_version

__all__ = ('DLL_PATH', 'DLL', 'dlclose', 'CFUNC')

this_dir = module_path()
arch_dir = this_dir/(arch or "")

try:
    from ...__config__ import config  # type: ignore[attr-defined]
    config_var = config.get("LIBUSB")
    del config
    if config_var in (None, "", "None"): raise ImportError()
except ImportError:
    version = macos_version()
    if version < (10, 13):
        raise NotImplementedError("This OS version ({}) is not supported!"
                                  .format(".".join(str(x) for x in version)))
    ver_dir = ""
    DLL_PATH = arch_dir/ver_dir/"libusb-1.0.dylib"
    if arch is None or not DLL_PATH.exists():
        raise ImportError(f"Unsupported platform: {platform.system()}, "
                          f"machine: {platform.machine()}")
else:
    DLL_PATH = Path(config_var)
