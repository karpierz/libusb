# Copyright (c) 2016-2020 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/licenses/Zlib

# libusb stress test program to perform simple stress tests
# Copyright © 2012 Toby Gray <toby.gray@realvnc.com>
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
from testlib import test_result, test_ctx, test_spec


def test_init_and_exit(tctx: test_ctx) -> int:
    """Test that creates and destroys a single concurrent context
    10000 times."""

    for i in range(10000):
        ctx = ct.POINTER(usb.context)()
        r = usb.init(ct.byref(ctx))
        if r != usb.LIBUSB_SUCCESS:
            testlib.logf(tctx, "Failed to init libusb on iteration "
                         "{:d}: {:d}", i, r)
            return test_result.TEST_STATUS_FAILURE
        usb.exit(ctx)

    return test_result.TEST_STATUS_SUCCESS


def test_get_device_list(tctx: test_ctx) -> int:
    """Tests that devices can be listed 1000 times."""

    ctx = ct.POINTER(usb.context)()
    r = usb.init(ct.byref(ctx))
    if r != usb.LIBUSB_SUCCESS:
        testlib.logf(tctx, "Failed to init libusb: {:d}", r)
        return test_result.TEST_STATUS_FAILURE

    for i in range(1000):
        device_list = ct.POINTER(ct.POINTER(usb.device))()
        list_size = usb.get_device_list(ctx, ct.byref(device_list))
        if list_size < 0 or not device_list:
            testlib.logf(tctx, "Failed to get device list on iteration "
                         "{:d}: {:d} ({:#x})", i, -list_size, device_list)
            return test_result.TEST_STATUS_FAILURE
        usb.free_device_list(device_list, 1)

    usb.exit(ctx)
    return test_result.TEST_STATUS_SUCCESS


def test_many_device_lists(tctx: test_ctx) -> int:
    """Tests that 100 concurrent device lists can be open at a time."""

    LIST_COUNT = 100

    ctx = ct.POINTER(usb.context)()
    r = usb.init(ct.byref(ctx))
    if r != usb.LIBUSB_SUCCESS:
        testlib.logf(tctx, "Failed to init libusb: {:d}", r)
        return test_result.TEST_STATUS_FAILURE

    device_lists = (ct.POINTER(ct.POINTER(usb.device)) * LIST_COUNT)()

    # Create the 100 device lists.
    for i in range(LIST_COUNT):
        list_size = usb.get_device_list(ctx, ct.byref(device_lists[i]))
        if list_size < 0 or not device_lists[i]:
            testlib.logf(tctx, "Failed to get device list on iteration "
                         "{:d}: {:d} ({:#x})", i, -list_size, device_lists[i])
            return test_result.TEST_STATUS_FAILURE

    # Destroy the 100 device lists.
    for i in range(LIST_COUNT):
        if device_lists[i]:
            usb.free_device_list(device_lists[i], 1)
            device_lists[i] = None

    usb.exit(ctx)
    return test_result.TEST_STATUS_SUCCESS


def test_default_context_change(tctx: test_ctx) -> int:
    """Tests that the default context (used for various things including
    logging) works correctly when the first context created in a
    process is destroyed."""

    ctx = ct.POINTER(usb.context)()
    for i in range(100):

        # First create a new context
        r = usb.init(ct.byref(ctx))
        if r != usb.LIBUSB_SUCCESS:
            testlib.logf(tctx, "Failed to init libusb: {:d}", r)
            return test_result.TEST_STATUS_FAILURE

        # Enable debug output, to be sure to use the context
        usb.set_option(None, usb.LIBUSB_OPTION_LOG_LEVEL, usb.LIBUSB_LOG_LEVEL_DEBUG)
        usb.set_option(ctx,  usb.LIBUSB_OPTION_LOG_LEVEL, usb.LIBUSB_LOG_LEVEL_DEBUG)

        # Now create a reference to the default context
        r = usb.init(None)
        if r != usb.LIBUSB_SUCCESS:
            testlib.logf(tctx, "Failed to init libusb: {:d}", r)
            return test_result.TEST_STATUS_FAILURE

        # Destroy the first context
        usb.exit(ctx)
        # Destroy the default context
        usb.exit(None)

    return test_result.TEST_STATUS_SUCCESS


# Fill in the list of tests.

tests = [
    test_spec("init_and_exit", test_init_and_exit),
    test_spec("get_device_list", test_get_device_list),
    test_spec("many_device_lists", test_many_device_lists),
    test_spec("default_context_change", test_default_context_change),
]


def main(argv=sys.argv):
    return testlib.run_tests(argv, tests)


sys.exit(main())
