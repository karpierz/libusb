# Copyright (c) 2016-2020 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/licenses/zlib

from ._platform import DLL_PATH, DLL, dlclose

try:
    dll = DLL(DLL_PATH)
except OSError as exc:
    raise exc
except Exception as exc:
    raise OSError("{}".format(exc))
