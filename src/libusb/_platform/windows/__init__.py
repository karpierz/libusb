# Copyright (c) 2016 Adam Karpierz
# SPDX-License-Identifier: Zlib

import platform
from pathlib import Path

from utlx import module_path
from utlx.platform import arch
from utlx.platform.capi import DLL, dlclose, CFUNC
from utlx.platform.windows import winapi

__all__ = ('DLL_PATH', 'DLL', 'dlclose', 'CFUNC', 'winapi')

this_dir = module_path()
arch_dir = this_dir/(arch or "")

try:
    from ...__config__ import config  # type: ignore[attr-defined]
    config_var = config.get("LIBUSB")
    del config
    if config_var in (None, "", "None"): raise ImportError()
except ImportError:
    DLL_PATH = arch_dir/"libusb-1.0.dll"
    if arch is None or not DLL_PATH.exists():
        raise ImportError(f"Unsupported platform: {platform.system()}, "
                          f"machine: {platform.machine()}")
else:
    DLL_PATH = Path(config_var)
