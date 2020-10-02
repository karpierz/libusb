# Copyright (c) 2016-2020 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/licenses/Zlib

# libusb test library helper functions
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
import os
from libusb._platform import is_windows, defined

if is_windows and defined("_WIN32_WCE"):
    # No support for selective redirection of STDOUT on WinCE.
    DISABLE_STDOUT_REDIRECTION = True
else:
    STDOUT_FILENO = sys.__stdout__.fileno()
    STDERR_FILENO = sys.__stderr__.fileno()
INVALID_FD = -1


class test_result:
    """Values returned from a test function to indicate test result"""

    # Indicates that the test ran successfully.
    TEST_STATUS_SUCCESS = 0
    # Indicates that the test failed one or more test.
    TEST_STATUS_FAILURE = 1
    # Indicates that an unexpected error occurred.
    TEST_STATUS_ERROR = 2
    # Indicates that the test can't be run. For example this may be
    # due to no suitable device being connected to perform the tests.
    TEST_STATUS_SKIP = 3


class test_ctx:
    """Context for test library functions"""

    def __init__(self):
        # Setup default mode of operation
        self.test_names = None
        self.list_tests = False
        self.verbose = False
        self.old_stdout = INVALID_FD
        self.old_stderr = INVALID_FD
        self.output_file = sys.__stdout__
        self.null_fd = INVALID_FD


class test_spec:
    """Structure holding a test description."""

    def __init__(self, name, function):
        # Human readable name of the test.
        self.name = name
        # The test library will call this function to run the test.
        # It has one parameter of test_ctx type.
        # Should return test_result.TEST_STATUS_SUCCESS on success or
        # another test_result.TEST_STATUS_* value.
        self.function = function


def _test_result_to_str(result: test_result) -> str:
    """Converts a test result code into a human readable string."""

    _test_result_str = {
        test_result.TEST_STATUS_SUCCESS: "Success",
        test_result.TEST_STATUS_FAILURE: "Failure",
        test_result.TEST_STATUS_ERROR:   "Error",
        test_result.TEST_STATUS_SKIP:    "Skip",
    }

    return _test_result_str.get(result, "Unknown")


def _print_usage(argv):
    print("Usage: {} [-l] [-v] [<test_name> ...]".format(
          argv[0] if len(argv) > 0 else "test_*"))
    print("   -l   List available tests")
    print("   -v   Don't redirect STDERR/STDOUT during tests")


def _cleanup_test_output(ctx: test_ctx):

    if not defined("DISABLE_STDOUT_REDIRECTION"):

        if not ctx.verbose:

            if ctx.old_stdout != INVALID_FD:
                try:
                    os.dup2(ctx.old_stdout, STDOUT_FILENO)
                except OSError:
                    pass
                ctx.old_stdout = INVALID_FD

            if ctx.old_stderr != INVALID_FD:
                try:
                    os.dup2(ctx.old_stderr, STDERR_FILENO)
                except OSError:
                    pass
                ctx.old_stderr = INVALID_FD

            if ctx.null_fd != INVALID_FD:
                try:
                    os.close(ctx.null_fd)
                except OSError:
                    pass
                ctx.null_fd = INVALID_FD

            if ctx.output_file != sys.__stdout__:
                try:
                    ctx.output_file.close()
                except OSError:
                    pass
                ctx.output_file = sys.__stdout__

    #endif


def _setup_test_output(ctx: test_ctx) -> int:
    """Setup test output handles
    \return zero on success, non-zero on failure"""

    if not defined("DISABLE_STDOUT_REDIRECTION"):

        # Stop output to stdout and stderr from being displayed
        # if using non-verbose output

        if not ctx.verbose:

            # Keep a copy of STDOUT and STDERR

            try:
                ctx.old_stdout = os.dup(STDOUT_FILENO)
            except OSError as exc:
                ctx.old_stdout = INVALID_FD
                print("Failed to duplicate stdout handle: {:d}".format(exc.errno))
                return 1

            try:
                ctx.old_stderr = os.dup(STDERR_FILENO)
            except OSError as exc:
                ctx.old_stderr = INVALID_FD
                _cleanup_test_output(ctx)
                print("Failed to duplicate stderr handle: {:d}".format(exc.errno))
                return 1

            # Redirect STDOUT_FILENO and STDERR_FILENO to /dev/null or "nul"

            try:
                ctx.null_fd = os.open(os.devnull, os.O_WRONLY)
            except OSError as exc:
                ctx.null_fd = INVALID_FD
                _cleanup_test_output(ctx)
                print("Failed to open null handle: {:d}".format(exc.errno))
                return 1

            try:
                os.dup2(ctx.null_fd, STDOUT_FILENO)
                os.dup2(ctx.null_fd, STDERR_FILENO)
            except OSError:
                _cleanup_test_output(ctx)
                return 1

            try:
                ctx.output_file = os.fdopen(ctx.old_stdout, "w")
            except OSError as exc:
                ctx.output_file = sys.__stdout__
                _cleanup_test_output(ctx)
                print("Failed to open FILE for output handle: {:d}".format(exc.errno))
                return 1

    #endif

    return 0


def logf(ctx: test_ctx, fmt: str, *args):
    """Logs some test information or state"""

    print(fmt.format(*args), file=ctx.output_file)
    ctx.output_file.flush()


def run_tests(argv: list, tests: list) -> int:
    """Runs the tests provided.

    Before running any tests argv will be processed
    to determine the mode of operation.

    \param argv The argv from main
    \param tests A NULL_TEST terminated array of tests
    \return 0 on success, non-zero on failure"""

    ctx = test_ctx()

    # Parse command line options
    for j, arg in enumerate(argv[1:]):
        if arg[0] in ('-', '/') and len(arg) >= 2:
            opt = arg[1]
            if opt == 'l':
                ctx.list_tests = True
                break;
            elif opt == 'v':
                ctx.verbose = True
                break;
            else:
                print("Unknown option: '{}'".format(arg))
                _print_usage(argv)
                return 1
        else:
            # End of command line options, remaining must be list
            # of tests to run
            ctx.test_names = argv[j + 1:]
            break

    # Validate command line options
    if ctx.test_names and ctx.list_tests:
        print("List of tests requested but test list provided")
        _print_usage(argv)
        return 1

    # Setup test log output
    r = _setup_test_output(ctx)
    if r != 0:
        return r

    # Act on any options not related to running tests

    if ctx.list_tests:
        for test in tests:
            logf(ctx, test.name)
        _cleanup_test_output(ctx)
        return 0

    # Run any requested tests

    run_count = 0
    pass_count = 0
    fail_count = 0
    error_count = 0
    skip_count = 0

    for test in tests:

        if ctx.test_names:
            # Filtering tests to run, check if this is one of them
            for test_name in ctx.test_names:
                if test_name == test.name:
                    # Matches a requested test name
                    break
            else:
                # Failed to find a test match, so do the next loop iteration
                continue

        logf(ctx, "Starting test run: {}...", test.name)
        result = test.function(ctx)
        logf(ctx, "{} ({:d})", _test_result_to_str(result), result)
        if   result == test_result.TEST_STATUS_SUCCESS: pass_count += 1
        elif result == test_result.TEST_STATUS_FAILURE: fail_count += 1
        elif result == test_result.TEST_STATUS_ERROR: error_count += 1
        elif result == test_result.TEST_STATUS_SKIP: skip_count += 1
        run_count += 1

    logf(ctx, "---")
    logf(ctx, "Ran {:d} tests", run_count)
    logf(ctx, "Passed {:d} tests", pass_count)
    logf(ctx, "Failed {:d} tests", fail_count)
    logf(ctx, "Error in {:d} tests", error_count)
    logf(ctx, "Skipped {:d} tests", skip_count)

    _cleanup_test_output(ctx)

    return int(pass_count != run_count)
