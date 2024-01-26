# Copyright (c) 2016 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/license/zlib

from ._platform import DLL_PATH, DLL, dlclose

try:
    dll = DLL(DLL_PATH)
except OSError as exc:  # pragma: no cover
    raise exc
except Exception as exc:  # pragma: no cover
    raise OSError("{}".format(exc)) from None
