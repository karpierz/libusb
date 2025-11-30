# Copyright (c) 2016 Adam Karpierz
# SPDX-License-Identifier: Zlib

import platform
from pathlib import Path

from utlx import module_path
from utlx.platform import arch
from utlx.platform.capi import DLL, dlclose, CFUNC

__all__ = ('DLL_PATH', 'DLL', 'dlclose', 'CFUNC')

this_dir = module_path()
arch_dir = this_dir/(arch or "")

try:
    from ...__config__ import config  # type: ignore[attr-defined]
    DLL_PATH = config.get("LIBUSB", None)
    del config
    if DLL_PATH is None or DLL_PATH in ("", "None"):
        raise ImportError()  # pragma: no cover
    DLL_PATH = Path(DLL_PATH)
except ImportError:
    DLL_PATH = arch_dir/"libusb-1.0.so"
    if arch is None or not DLL_PATH.exists():
        raise ImportError(f"Unsupported platform: {platform.system()}, "
                          f"machine: {platform.machine()}")
