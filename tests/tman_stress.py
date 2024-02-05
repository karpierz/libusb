# Copyright (c) 2016 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/license/zlib

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
from testlib import test_result, test_spec


def test_init_and_exit() -> test_result:
    """Test that creates and destroys a single concurrent context
    10000 times."""

    for i in range(10000):
        ctx = ct.POINTER(usb.context)()
        r = (usb.init_context(ct.byref(ctx), None, 0)
             if hasattr(usb, "init_context") else
             usb.init(ct.byref(ctx)))
        if r != usb.LIBUSB_SUCCESS:
            testlib.logf("Failed to init libusb on iteration {:d}: {:d}", i, r)
            return test_result.TEST_STATUS_FAILURE
        usb.exit(ctx)

    return test_result.TEST_STATUS_SUCCESS


def test_get_device_list() -> test_result:
    """Tests that devices can be listed 1000 times."""

    ctx = ct.POINTER(usb.context)()
    r = (usb.init_context(ct.byref(ctx), None, 0)
         if hasattr(usb, "init_context") else
         usb.init(ct.byref(ctx)))
    if r != usb.LIBUSB_SUCCESS:
        testlib.logf("Failed to init libusb: {:d}", r)
        return test_result.TEST_STATUS_FAILURE

    for i in range(1000):
        device_list = ct.POINTER(ct.POINTER(usb.device))()
        list_size = usb.get_device_list(ctx, ct.byref(device_list))
        if list_size < 0 or not device_list:
            testlib.logf("Failed to get device list on iteration "
                         "{:d}: {:d} ({:#x})", i, -list_size, device_list)
            usb.exit(ctx)
            return test_result.TEST_STATUS_FAILURE
        usb.free_device_list(device_list, 1)

    usb.exit(ctx)
    return test_result.TEST_STATUS_SUCCESS


def test_many_device_lists() -> test_result:
    """Tests that 100 concurrent device lists can be open at a time."""

    LIST_COUNT = 100

    ctx = ct.POINTER(usb.context)()
    r = (usb.init_context(ct.byref(ctx), None, 0)
         if hasattr(usb, "init_context") else
         usb.init(ct.byref(ctx)))
    if r != usb.LIBUSB_SUCCESS:
        testlib.logf("Failed to init libusb: {:d}", r)
        return test_result.TEST_STATUS_FAILURE

    result = test_result.TEST_STATUS_SUCCESS
    device_lists = (ct.POINTER(ct.POINTER(usb.device)) * LIST_COUNT)()

    # Create the 100 device lists.
    for i in range(LIST_COUNT):
        list_size = usb.get_device_list(ctx, ct.byref(device_lists[i]))
        if list_size < 0 or not device_lists[i]:
            testlib.logf("Failed to get device list on iteration "
                         "{:d}: {:d} ({:#x})", i, -list_size, device_lists[i])
            result = test_result.TEST_STATUS_FAILURE
            break

    # Destroy the 100 device lists.
    for i in range(LIST_COUNT):
        if device_lists[i]:
            usb.free_device_list(device_lists[i], 1)

    usb.exit(ctx)
    return result


def test_default_context_change() -> test_result:
    """Tests that the default context (used for various things including
    logging) works correctly when the first context created in a
    process is destroyed."""

    for i in range(100):
        # Enable debug output on new context, to be sure to use the context
        options = (usb.init_option * 1)()
        options[0].option = usb.LIBUSB_OPTION_LOG_LEVEL
        options[0].value.ival = usb.LIBUSB_LOG_LEVEL_DEBUG
        num_options = 1

        # First create a new context
        ctx = ct.POINTER(usb.context)()
        r = (usb.init_context(ct.byref(ctx), options, num_options)
             if hasattr(usb, "init_context") else
             usb.init(ct.byref(ctx)))
        if r != usb.LIBUSB_SUCCESS:
            testlib.logf("Failed to init libusb: {:d}", r)
            return test_result.TEST_STATUS_FAILURE

        if not hasattr(usb, "init_context"):
            # Enable debug output on new context, to be sure to use the context
            usb.set_debug(ctx, usb.LIBUSB_LOG_LEVEL_DEBUG)
            # Enable debug output on the default context. This should work even before
            # the context has been created.
            usb.set_debug(None, usb.LIBUSB_LOG_LEVEL_DEBUG)

        # Now create a reference to the default context
        r = (usb.init_context(None, options, num_options)
             if hasattr(usb, "init_context") else
             usb.init(None))
        if r != usb.LIBUSB_SUCCESS:
            testlib.logf("Failed to init libusb: {:d}", r)
            usb.exit(ctx)
            return test_result.TEST_STATUS_FAILURE

        # Destroy the first context
        usb.exit(ctx)
        # Destroy the default context
        usb.exit(None)

    return test_result.TEST_STATUS_SUCCESS


# Fill in the list of tests.

tests = [
    test_spec("init_and_exit",          test_init_and_exit),
    test_spec("get_device_list",        test_get_device_list),
    test_spec("many_device_lists",      test_many_device_lists),
    test_spec("default_context_change", test_default_context_change),
]


def main(argv=sys.argv[1:]):
    return testlib.run_tests(argv, tests)


if __name__.rpartition(".")[-1] == "__main__":
    sys.exit(main())
