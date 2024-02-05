# Copyright (c) 2023 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/license/zlib

# Unit tests for libusb.init_context
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

ENABLE_LOGGING = 1

import libusb as usb
import testlib
from testlib import test_result, test_spec
from libusb._platform import defined, is_posix, is_windows


def test_init_context_basic() -> test_result:

    test_ctx = ct.POINTER(usb.context)()

    # test basic functionality
    testlib.EXPECT_SUCCESS(test_ctx, usb.init_context(ct.byref(test_ctx), None, 0)
                                     if hasattr(usb, "init_context") else
                                     usb.init(ct.byref(test_ctx)))

    return testlib.TEST_CLEAN_EXIT(test_ctx, test_result.TEST_STATUS_SUCCESS)


def test_init_context_log_level() -> test_result:

    test_ctx = ct.POINTER(usb.context)()

    if hasattr(usb, "init_context"):
        options = (usb.init_option * 1)()
        options[0].option = usb.LIBUSB_OPTION_LOG_LEVEL
        options[0].value.ival = usb.LIBUSB_LOG_LEVEL_ERROR
        # test basic functionality
        testlib.EXPECT_SUCCESS(test_ctx, usb.init_context(ct.byref(test_ctx), options, 1))
    else:
        # test basic functionality
        testlib.EXPECT_SUCCESS(test_ctx, usb.init(ct.byref(test_ctx)))
        testlib.EXPECT_SUCCESS(test_ctx, usb.set_option(test_ctx,
                                                        usb.LIBUSB_OPTION_LOG_LEVEL,
                                                        usb.LIBUSB_LOG_LEVEL_ERROR))

    if defined("ENABLE_LOGGING") and not defined("ENABLE_DEBUG_LOGGING"):
        testlib.EXPECT_EQ(test_ctx, test_ctx.contents.debug, usb.LIBUSB_LOG_LEVEL_ERROR)

    return testlib.TEST_CLEAN_EXIT(test_ctx, test_result.TEST_STATUS_SUCCESS)


@usb.log_cb
def test_log_cb(ctx, level, str):
    pass


def test_init_context_log_cb() -> test_result:

    if hasattr(usb, "init_context"):
        test_ctx = ct.POINTER(usb.context)()

        options = (usb.init_option * 1)()
        options[0].option = usb.LIBUSB_OPTION_LOG_CB
        options[0].value.log_cbval = test_log_cb
        # test basic functionality
        testlib.EXPECT_SUCCESS(test_ctx, usb.init_context(ct.byref(test_ctx), options, 1))

        if defined("ENABLE_LOGGING") and not defined("ENABLE_DEBUG_LOGGING"):
            testlib.EXPECT_EQ(test_ctx, test_ctx.contents.log_handler, test_log_cb)

        return testlib.TEST_CLEAN_EXIT(test_ctx, test_result.TEST_STATUS_SUCCESS)
    else:
        return test_result.TEST_STATUS_SKIP


tests = [
    test_spec("test_init_context_basic",     test_init_context_basic),
    test_spec("test_init_context_log_level", test_init_context_log_level),
    test_spec("test_init_context_log_cb",    test_init_context_log_cb),
]


def main(argv=sys.argv[1:]):
    return testlib.run_tests(argv, tests)


if __name__.rpartition(".")[-1] == "__main__":
    sys.exit(main())
