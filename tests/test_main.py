# Copyright (c) 2016 Adam Karpierz
# SPDX-License-Identifier: Zlib

import unittest
from unittest import mock
import sys
from functools import partial

import libusb
from utlx import run
from utlx.platform import is_windows
run = partial(run, check=False)

from . import test_dir


class MainTestCase(unittest.TestCase):

    def setUp(self):
        pass

    @unittest.skipUnless(False, "Windows-only test")
    def test_dll_nonexistent(self):
        sys.modules.pop("libusb.__config__", None)
        with mock.patch("libusb.__config__.config",
                        return_value={"LIBUSB":
                                      str(test_dir/".nonexistent")}), \
             self.assertRaises(ImportError) as exc:
            sys.modules.pop("libusb._platform.windows", None)
            sys.modules.pop("libusb._platform", None)
            import libusb._platform
        sys.modules.pop("libusb._platform.windows", None)
        sys.modules.pop("libusb._platform", None)
        import libusb._platform
        self.assertIn("Shared library not found: ", str(exc.exception))

    @unittest.skipUnless(is_windows, "Windows-only test")
    def test_arch_nonexistent(self):
        with mock.patch("utlx.platform.arch", return_value=None), \
             self.assertRaises(ImportError) as exc:
            sys.modules.pop("libusb._platform.windows", None)
            sys.modules.pop("libusb._platform", None)
            import libusb._platform
        sys.modules.pop("libusb._platform.windows", None)
        sys.modules.pop("libusb._platform", None)
        import libusb._platform
        self.assertIn("Unsupported platform: ", str(exc.exception))

    def test_init_context(self):
        output = run(sys.executable, test_dir/"tman_init_context.py")
        self.assertEqual(output.returncode, 0)
        print()

    def test_set_option(self):
        output = run(sys.executable, test_dir/"tman_set_option.py")
        self.assertEqual(output.returncode, 0)
        print()

    def test_stress(self):
        output = run(sys.executable, test_dir/"tman_stress.py")
        self.assertEqual(output.returncode, 0)
        print()
