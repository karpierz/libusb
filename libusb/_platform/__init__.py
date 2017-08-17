# coding: utf-8

from sys import platform

if bool(platform.win32_ver()[0]):
    from ._windows import DLL_PATH, DLL, CFUNC, dlclose, timeval
elif platform.startswith("linux"):
    from ._linux   import DLL_PATH, DLL, CFUNC, dlclose, timeval
elif platform == "darwin":
    from ._osx     import DLL_PATH, DLL, CFUNC, dlclose, timeval
else:
    raise ImportError("unsupported platform")

del platform

# eof
