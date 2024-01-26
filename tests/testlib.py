# Copyright (c) 2016 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/license/zlib

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


class test_spec:
    """Structure holding a test description."""

    def __init__(self, name, function):
        # Human readable name of the test.
        self.name = name
        # The test library will call this function to run the test.
        # Should return test_result.TEST_STATUS_SUCCESS on success or
        # another test_result.TEST_STATUS_* value.
        self.function = function


def test_result_to_str(result: test_result) -> str:
    """Converts a test result code into a human readable string."""
    test_result_str = {
        test_result.TEST_STATUS_SUCCESS: "Success",
        test_result.TEST_STATUS_FAILURE: "Failure",
        test_result.TEST_STATUS_ERROR:   "Error",
        test_result.TEST_STATUS_SKIP:    "Skip",
    }

    return test_result_str.get(result, "Unknown")


def print_usage(progname: str):
    print("Usage: {} [-l] [-v] [<test_name> ...]".format(progname))
    print("   -l   List available tests")
    print("   -v   Don't redirect STDERR before running tests")
    print("   -h   Display this help and exit")


def logf(fmt: str, *args):
    """Logs some test information or state"""
    print(fmt.format(*args), file=sys.stdout)
    sys.stdout.flush()


def run_tests(argv: list, tests: list) -> int:
    """Runs the tests provided.

    Before running any tests argv will be processed
    to determine the mode of operation.

    \param argv The argv from main
    \param tests A NULL_TEST terminated array of tests
    \return 0 on success, non-zero on failure"""

    # Setup default mode of operation
    test_names = None
    list_tests = False
    verbose = False

    # Parse command line options
    for j, arg in enumerate(argv):
        if arg[0] in ('-', '/'):
            if len(arg) == 2:
                opt = arg[1]
                if opt == 'l':
                    list_tests = True
                    continue
                elif opt == 'v':
                    verbose = True
                    continue
                elif opt == 'h':
                    print_usage(sys.argv[0])
                    return 0

            print("Unknown option: '{}'".format(arg), file=sys.stderr)
            print_usage(sys.argv[0])
            return 1
        else:
            # End of command line options, remaining must be list
            # of tests to run
            test_names = argv[j:]
            break

    # Validate command line options
    if test_names and list_tests:
        print("List of tests requested but test list provided", file=sys.stderr)
        print_usage(sys.argv[0])
        return 1

    # Setup test log output
    if not verbose:
        try:
            sys.stderr.close()
        except: pass
        try:
            sys.stderr = open(os.devnull, "w")
        except Exception as exc:
            print("Failed to open null handle: {:d}".format(exc.errno))
            return 1

    # Act on any options not related to running tests

    if list_tests:
        for test in tests:
            logf("{}", test.name)
        return 0

    # Run any requested tests

    run_count = 0
    pass_count = 0
    fail_count = 0
    error_count = 0
    skip_count = 0

    for test in tests:

        if test_names:
            # Filtering tests to run, check if this is one of them
            for test_name in test_names:
                if test_name == test.name:
                    # Matches a requested test name
                    break
            else:
                # Failed to find a test match, so do the next loop iteration
                continue

        logf("Starting test run: {}...", test.name)
        result = test.function()
        logf("{} ({:d})", test_result_to_str(result), result)
        if   result == test_result.TEST_STATUS_SUCCESS: pass_count += 1
        elif result == test_result.TEST_STATUS_FAILURE: fail_count += 1
        elif result == test_result.TEST_STATUS_ERROR: error_count += 1
        elif result == test_result.TEST_STATUS_SKIP: skip_count += 1
        run_count += 1

    logf("---")
    logf("Ran {:d} tests", run_count)
    logf("Passed {:d} tests", pass_count)
    logf("Failed {:d} tests", fail_count)
    logf("Error in {:d} tests", error_count)
    logf("Skipped {:d} tests", skip_count)

    return int(pass_count != run_count)
