# Copyright (c) 2023 Adam Karpierz
# SPDX-License-Identifier: Zlib

# Unit tests for libusb_set_option
# Copyright © 2023 Nathan Hjelm <hjelmn@cs.unm.edu>
# Copyright © 2023 Google, LLC. All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import sys
import ctypes as ct

import libusb as usb
import testlib
from testlib import test_result, test_spec

# extern uint32_t libusb_testonly_fake_running_version;
# extern uint32_t libusb_testonly_using_running_interface_version;
# extern uint32_t libusb_testonly_using_running_device_version;
# extern bool     libusb_testonly_clear_running_version_cache;
usb.testonly_fake_running_version            = ct.c_uint32.in_dll(usb.dll,
                                               "libusb_testonly_fake_running_version")
usb.testonly_using_running_interface_version = ct.c_uint32.in_dll(usb.dll,
                                               "libusb_testonly_using_running_interface_version")
usb.testonly_using_running_device_version    = ct.c_uint32.in_dll(usb.dll,
                                               "libusb_testonly_using_running_device_version")
usb.testonly_clear_running_version_cache     = ct.c_bool.in_dll(usb.dll,
                                               "libusb_testonly_clear_running_version_cache")


def test_macos_version_fallback() -> test_result:

    test_ctx = ct.POINTER(usb.context)()

    usb.testonly_fake_running_version.value = 100001
    usb.testonly_clear_running_version_cache.value = True

    testlib.EXPECT_SUCCESS(test_ctx, usb.init_context(ct.byref(test_ctx), None, 0))
    testlib.EXPECT_EQ(test_ctx, usb.testonly_using_running_interface_version.value, 220)
    testlib.EXPECT_EQ(test_ctx, usb.testonly_using_running_device_version.value,    197)

    usb.exit(test_ctx)
    test_ctx = ct.POINTER(usb.context)()

    usb.testonly_fake_running_version.value = 100900

    testlib.EXPECT_SUCCESS(test_ctx, usb.init_context(ct.byref(test_ctx), None, 0))
    testlib.EXPECT_EQ(test_ctx, usb.testonly_using_running_interface_version.value, 650)
    testlib.EXPECT_EQ(test_ctx, usb.testonly_using_running_device_version.value,    650)

    usb.exit(test_ctx)
    test_ctx = ct.POINTER(usb.context)()

    usb.testonly_fake_running_version.value = 101200

    testlib.EXPECT_SUCCESS(test_ctx, usb.init_context(ct.byref(test_ctx), None, 0))
    testlib.EXPECT_EQ(test_ctx, usb.testonly_using_running_interface_version.value, 800)
    testlib.EXPECT_EQ(test_ctx, usb.testonly_using_running_device_version.value,    650)

    usb.exit(test_ctx)
    test_ctx = ct.POINTER(usb.context)()

    # Test a version smaller than 10.0. Initialization should fail.
    usb.testonly_fake_running_version.value = 99999

    error: int = usb.init_context(ct.byref(test_ctx), None, 0)
    testlib.EXPECT_NE(test_ctx, error, usb.LIBUSB_SUCCESS)

    testlib.TEST_CLEAN_EXIT(test_ctx, test_result.TEST_STATUS_SUCCESS)


tests = [
    test_spec("test_macos_version_fallback", test_macos_version_fallback),
]


def main(argv=sys.argv[1:]):
    return testlib.run_tests(argv, tests)


if __name__.rpartition(".")[-1] == "__main__":
    sys.exit(main())
