# Copyright (c) 2023 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/license/zlib

# Unit tests for libusb.set_option
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
from libusb._platform import defined, is_posix, is_linux, is_windows


def test_set_log_level_basic() -> test_result:

    if defined("ENABLE_LOGGING") and not defined("ENABLE_DEBUG_LOGGING"):

        test_ctx = ct.POINTER(usb.context)()

        # unset LIBUSB_DEBUG if it is set
        testlib.unsetenv("LIBUSB_DEBUG")

        # test basic functionality
        testlib.EXPECT_SUCCESS(test_ctx, usb.init_context(ct.byref(test_ctx), None, 0)
                                         if hasattr(usb, "init_context") else
                                         usb.init(ct.byref(test_ctx)))
        testlib.EXPECT_SUCCESS(test_ctx, usb.set_option(test_ctx,
                                                        usb.LIBUSB_OPTION_LOG_LEVEL,
                                                        usb.LIBUSB_LOG_LEVEL_ERROR))
        testlib.EXPECT_EQ(test_ctx, test_ctx.contents.debug, usb.LIBUSB_LOG_LEVEL_ERROR)
        testlib.EXPECT_SUCCESS(test_ctx, usb.set_option(test_ctx,
                                                        usb.LIBUSB_OPTION_LOG_LEVEL,
                                                        usb.LIBUSB_LOG_LEVEL_NONE))
        testlib.EXPECT_EQ(test_ctx, test_ctx.contents.debug, usb.LIBUSB_LOG_LEVEL_NONE)

        return testlib.TEST_CLEAN_EXIT(test_ctx, test_result.TEST_STATUS_SUCCESS)
    else:
        return test_result.TEST_STATUS_SKIP


def test_set_log_level_default() -> test_result:

    if defined("ENABLE_LOGGING") and not defined("ENABLE_DEBUG_LOGGING"):
        test_ctx = ct.POINTER(usb.context)()

        if hasattr(usb, "init_context"):
            # set the default debug level
            testlib.EXPECT_SUCCESS(test_ctx, usb.set_option(None,
                                                            usb.LIBUSB_OPTION_LOG_LEVEL,
                                                            usb.LIBUSB_LOG_LEVEL_ERROR))
            testlib.EXPECT_SUCCESS(test_ctx, usb.init_context(ct.byref(test_ctx), None, 0))
        else:
            # set the default debug level
            testlib.EXPECT_SUCCESS(test_ctx, usb.init(ct.byref(test_ctx)))
            testlib.EXPECT_SUCCESS(test_ctx, usb.set_option(None,
                                                            usb.LIBUSB_OPTION_LOG_LEVEL,
                                                            usb.LIBUSB_LOG_LEVEL_ERROR))
        # check that debug level came from the default
        testlib.EXPECT_EQ(test_ctx, test_ctx.contents.debug, usb.LIBUSB_LOG_LEVEL_ERROR)

        # try to override the old log level. since this was set from the default it
        # should be possible to change it
        testlib.EXPECT_SUCCESS(test_ctx, usb.set_option(test_ctx,
                                                        usb.LIBUSB_OPTION_LOG_LEVEL,
                                                        usb.LIBUSB_LOG_LEVEL_NONE))
        testlib.EXPECT_EQ(test_ctx, test_ctx.contents.debug, usb.LIBUSB_LOG_LEVEL_NONE)

        return testlib.TEST_CLEAN_EXIT(test_ctx, test_result.TEST_STATUS_SUCCESS)
    else:
        return test_result.TEST_STATUS_SKIP


def test_set_log_level_env() -> test_result:

    if defined("ENABLE_LOGGING"):
        test_ctx = ct.POINTER(usb.context)()

        # check that libusb.set_option does not change the log level when it was set
        # from the environment.
        testlib.setenv("LIBUSB_DEBUG", "4", overwrite=False)
        testlib.EXPECT_SUCCESS(test_ctx, usb.init_context(ct.byref(test_ctx), None, 0)
                                         if hasattr(usb, "init_context") else
                                         usb.init(ct.byref(test_ctx)))
        if not defined("ENABLE_DEBUG_LOGGING"):
            testlib.EXPECT_EQ(test_ctx, test_ctx.contents.debug, 4)

        testlib.EXPECT_SUCCESS(test_ctx, usb.set_option(test_ctx,
                                                        usb.LIBUSB_OPTION_LOG_LEVEL,
                                                        usb.LIBUSB_LOG_LEVEL_ERROR))
        # environment variable should always override libusb.LIBUSB_OPTION_LOG_LEVEL if set
        if not defined("ENABLE_DEBUG_LOGGING"):
            testlib.EXPECT_EQ(test_ctx, test_ctx.contents.debug, 4)

        return testlib.TEST_CLEAN_EXIT(test_ctx, test_result.TEST_STATUS_SUCCESS)
    else:
        return test_result.TEST_STATUS_SKIP


def test_no_discovery() -> test_result:

    if is_linux:
        test_ctx = ct.POINTER(usb.context)()
        testlib.EXPECT_SUCCESS(test_ctx, usb.init_context(ct.byref(test_ctx), None, 0)
                                         if hasattr(usb, "init_context") else
                                         usb.init(ct.byref(test_ctx)))

        device_list = ct.POINTER(ct.POINTER(usb.device))()
        num_devices = usb.get_device_list(test_ctx, ct.byref(device_list))
        usb.free_device_list(device_list, 1)
        usb.exit(test_ctx)
        test_ctx = ct.POINTER(usb.context)()

        if num_devices == 0:
            testlib.logf("Warning: no devices found, the test will only verify "
                         "that setting LIBUSB_OPTION_NO_DEVICE_DISCOVERY succeeds.")

        testlib.EXPECT_GE(test_ctx, num_devices, 0)

        if hasattr(usb, "init_context"):
            testlib.EXPECT_SUCCESS(test_ctx, usb.set_option(None,
                                                            usb.LIBUSB_OPTION_NO_DEVICE_DISCOVERY))
            testlib.EXPECT_SUCCESS(test_ctx, usb.init_context(ct.byref(test_ctx), None, 0))
        else:
            testlib.EXPECT_SUCCESS(test_ctx, usb.init(ct.byref(test_ctx)))
            testlib.EXPECT_SUCCESS(test_ctx, usb.set_option(None,
                                                            usb.LIBUSB_OPTION_NO_DEVICE_DISCOVERY))

        device_list = ct.POINTER(ct.POINTER(usb.device))()
        num_devices = usb.get_device_list(test_ctx, ct.byref(device_list))
        usb.free_device_list(device_list, 1)

        testlib.EXPECT_EQ(test_ctx, num_devices, 0)

        return testlib.TEST_CLEAN_EXIT(test_ctx, test_result.TEST_STATUS_SUCCESS)
    else:
        return test_result.TEST_STATUS_SKIP


if defined("ENABLE_LOGGING") and not defined("ENABLE_DEBUG_LOGGING"):

    @usb.log_cb
    def test_log_cb(ctx, level, str):
        pass

#endif


def test_set_log_cb() -> test_result:

    if (defined("ENABLE_LOGGING") and not defined("ENABLE_DEBUG_LOGGING") and
        hasattr(usb, "init_context")):
        test_ctx = ct.POINTER(usb.context)()

        # set the log callback on the context
        testlib.EXPECT_SUCCESS(test_ctx, usb.init_context(ct.byref(test_ctx), None, 0))
        testlib.EXPECT_SUCCESS(test_ctx, usb.set_option(test_ctx,
                                                        usb.LIBUSB_OPTION_LOG_CB,
                                                        test_log_cb))

        # check that debug level came from the default
        testlib.EXPECT_EQ(test_ctx, test_ctx.contents.log_handler, test_log_cb)

        usb.exit(test_ctx)
        test_ctx = ct.POINTER(usb.context)()

        # set the log callback for all future contexts
        testlib.EXPECT_SUCCESS(test_ctx, usb.set_option(None,
                                                        usb.LIBUSB_OPTION_LOG_CB,
                                                        test_log_cb))
        testlib.EXPECT_SUCCESS(test_ctx, usb.init_context(ct.byref(test_ctx), None, 0))

        testlib.EXPECT_EQ(test_ctx, test_ctx.contents.log_handler, test_log_cb)

        return testlib.TEST_CLEAN_EXIT(test_ctx, test_result.TEST_STATUS_SUCCESS)
    else:
        return test_result.TEST_STATUS_SKIP


tests = [
    test_spec("test_set_log_level_basic",   test_set_log_level_basic),
    test_spec("test_set_log_level_env",     test_set_log_level_env),
    test_spec("test_no_discovery",          test_no_discovery),
    # since default options can't be unset, run this one last
    test_spec("test_set_log_level_default", test_set_log_level_default),
    test_spec("test_set_log_cb",            test_set_log_cb),
]


def main(argv=sys.argv[1:]):
    return testlib.run_tests(argv, tests)


if __name__.rpartition(".")[-1] == "__main__":
    sys.exit(main())
