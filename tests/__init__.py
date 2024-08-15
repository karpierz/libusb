# Copyright (c) 2016 Adam Karpierz
# SPDX-License-Identifier: Zlib

__all__ = ('top_dir', 'test_dir')

import sys, pathlib
sys.dont_write_bytecode = True
test_dir = pathlib.Path(__file__).resolve().parent
top_dir = test_dir.parent
del sys, pathlib
