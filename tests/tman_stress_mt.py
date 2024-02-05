# Copyright (c) 2023 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/license/zlib

# libusb multi-thread test program
# Copyright 2022-2023 Tormod Volden
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
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
from libusb._platform import defined, is_posix, is_windows
if is_windows: import win32

usb_error_name = lambda status: usb.error_name(status).decode("utf-8")

if is_posix:

    #include <pthread.h>
    thread_t = pthread_t
    thread_return_t = ct.c_void_p
    THREAD_RETURN_VALUE = NULL

    # thread_return_t (*thread_entry)(arg: ct.c_void_p)
    def thread_create(thread: ct.POINTER(thread_t),
                      thread_entry,
                      arg: ct.c_void_p) -> int:
        r = pthread_create(thread, NULL, thread_entry, arg)
        return 0 if r == 0 else -1

    def thread_join(thread: thread_t):
        pthread_join(thread, NULL)

    #include <stdatomic.h>

elif is_windows:

    thread_t = win32.HANDLE
    if defined("__CYGWIN__"):
        thread_return_t = win32.DWORD
    else:
       #thread_return_t = ct.c_uint
        thread_return_t = win32.DWORD
    THREAD_RETURN_VALUE = 0

    def thread_create(thread: ct.POINTER(thread_t),
                      thread_entry: win32.LPTHREAD_START_ROUTINE,
                      arg: ct.c_void_p) -> int:
        if defined("__CYGWIN__"):
            thread[0] = win32.CreateThread(None, 0, thread_entry, arg, 0, None)
        else:
           #thread[0] = ct.cast(_beginthreadex(None, 0, thread_entry, arg, 0, None), win32.HANDLE)
            thread[0] = win32.CreateThread(None, 0, thread_entry, arg, 0, None)
        return 0 if thread[0] else -1

    def thread_join(thread: thread_t):
        win32.WaitForSingleObject(thread, win32.INFINITE)
        win32.CloseHandle(thread)

    atomic_bool = ct.c_long # volatile
    #atomic_exchange = win32.InterlockedExchange
    def atomic_exchange(Target: ct.POINTER(win32.LONG), Value: win32.LONG) -> win32.LONG:
        Target.contents = win32.LONG(Value)
        return int(True)

#endif # PLATFORM_POSIX #

# Test that creates and destroys contexts repeatedly

NTHREADS = 8
ITERS = 64
MAX_DEVCOUNT = 128

class thread_info(ct.Structure):
    _fields_ = [
    ("number",    ct.c_int),
    ("enumerate", ct.c_int),
    ("devcount",  ct.c_ssize_t),
    ("err",       ct.c_int),
    ("iteration", ct.c_int),
]

tinfo     = (thread_info * NTHREADS)()
no_access = [atomic_bool(0)] * MAX_DEVCOUNT


def usbi_localize_device_descriptor(desc: usb.device_descriptor):
    # Function called by backend during device initialization to convert
    # multi-byte fields in the device descriptor to host-endian format.
    # Copied from libusbi.h as we want test to be realistic and not depend on internals.
    desc.bcdUSB    = usb.le16_to_cpu(desc.bcdUSB)
    desc.idVendor  = usb.le16_to_cpu(desc.idVendor)
    desc.idProduct = usb.le16_to_cpu(desc.idProduct)
    desc.bcdDevice = usb.le16_to_cpu(desc.bcdDevice)


if is_posix:

    def init_and_exit(arg: ct.c_void_p) -> thread_return_t:
        try:
            return _init_and_exit(arg)
        except:
            return THREAD_RETURN_VALUE

elif is_windows:

    @win32.LPTHREAD_START_ROUTINE
    def init_and_exit(arg: win32.LPVOID) -> thread_return_t:
        try:
            return _init_and_exit(arg)
        except:
            return THREAD_RETURN_VALUE

def _init_and_exit(arg):
    ti = ct.cast(arg, ct.POINTER(thread_info)).contents

    open_errors = ([usb.LIBUSB_ERROR_ACCESS,
                    usb.LIBUSB_ERROR_NOT_SUPPORTED,
                    usb.LIBUSB_ERROR_NOT_FOUND]
                   if is_windows else
                   [usb.LIBUSB_ERROR_ACCESS])

    for ti.iteration in range(ITERS):
        if ti.err != 0:
            break

        ctx = ct.POINTER(usb.context)()
        ti.err = (usb.init_context(ct.byref(ctx), None, 0)
                  if hasattr(usb, "init_context") else
                  usb.init(ct.byref(ctx)))
        if ti.err != 0:
            break

        if ti.enumerate:

            devs = ct.POINTER(ct.POINTER(usb.device))()
            ti.devcount = usb.get_device_list(ctx, ct.byref(devs))
            if ti.devcount < 0:
                ti.err = ti.devcount
                break

            for i in range(ti.devcount):
                if ti.err != 0:
                    break

                dev: ct.POINTER(usb.device) = devs[i]

                desc = usb.device_descriptor()
                ti.err = usb.get_device_descriptor(dev, ct.byref(desc))
                if ti.err != 0:
                    break

                if no_access[i].value:
                    continue

                dev_handle = ct.POINTER(usb.device_handle)()
                open_err: int = usb.open(dev, ct.byref(dev_handle))
                if open_err in open_errors:
                    # Use atomic swap to ensure we print warning only once across all threads.
                    # This is a warning and not a hard error because it should be fine to run tests
                    # even if we don't have access to some devices.
                    if not atomic_exchange(ct.pointer(no_access[i]), True):
                        print("No access to device {:04x}:{:04x}, skipping transfer "
                              "tests.".format(desc.idVendor, desc.idProduct), file=sys.stderr)
                    continue

                if open_err != 0:
                    ti.err = open_err
                    break

                # Request raw descriptor via control transfer.
                # This tests opening, transferring and closing from multiple threads in parallel.
                raw_desc = usb.device_descriptor()
                raw_desc_len: int = usb.get_descriptor(dev_handle, usb.LIBUSB_DT_DEVICE, 0,
                                                       ct.cast(ct.byref(raw_desc),
                                                               ct.POINTER(ct.c_ubyte)),
                                                       ct.sizeof(raw_desc))
                try:
                    if raw_desc_len < 0:
                        ti.err = raw_desc_len
                        raise AssertionError()

                    if raw_desc_len != ct.sizeof(raw_desc):
                        print("Thread {}: device {}: unexpected raw descriptor length {}".format(
                              ti.number, i, raw_desc_len), file=sys.stderr)
                        ti.err = usb.LIBUSB_ERROR_OTHER
                        raise AssertionError()

                    usbi_localize_device_descriptor(raw_desc)

                    def ASSERT_EQ(field1, field2):
                        if field1 != field2:
                            print("Thread {}: device {}: mismatch in field {}: {} != {}".format(
                                  ti.number, i, field1.__name__, field1, field2), file=sys.stderr)
                            ti.err = usb.LIBUSB_ERROR_OTHER
                            raise AssertionError()

                    ASSERT_EQ(raw_desc.bLength, desc.bLength)
                    ASSERT_EQ(raw_desc.bDescriptorType, desc.bDescriptorType)
                    if not is_windows:
                        # these are hardcoded by the winusbx HID backend
                        ASSERT_EQ(raw_desc.bcdUSB, desc.bcdUSB)
                        ASSERT_EQ(raw_desc.bDeviceClass, desc.bDeviceClass)
                        ASSERT_EQ(raw_desc.bDeviceSubClass, desc.bDeviceSubClass)
                        ASSERT_EQ(raw_desc.bDeviceProtocol, desc.bDeviceProtocol)
                        ASSERT_EQ(raw_desc.bMaxPacketSize0, desc.bMaxPacketSize0)
                        ASSERT_EQ(raw_desc.bcdDevice, desc.bcdDevice)
                    #endif
                    ASSERT_EQ(raw_desc.idVendor, desc.idVendor)
                    ASSERT_EQ(raw_desc.idProduct, desc.idProduct)
                    ASSERT_EQ(raw_desc.iManufacturer, desc.iManufacturer)
                    ASSERT_EQ(raw_desc.iProduct, desc.iProduct)
                    ASSERT_EQ(raw_desc.iSerialNumber, desc.iSerialNumber)
                    ASSERT_EQ(raw_desc.bNumConfigurations, desc.bNumConfigurations)

                except AssertionError:
                    usb.close(dev_handle)

            usb.free_device_list(devs, 1)

        usb.exit(ctx)

    return THREAD_RETURN_VALUE


def test_multi_init(enumer: int) -> int:

    threadId = [thread_t()] * NTHREADS

    errs = 0
    last_devcount     = 0
    devcount_mismatch = 0
    access_failures   = 0

    print("Starting {} threads".format(NTHREADS))
    for t, thread in enumerate(threadId):
        tinfo[t].err       = 0
        tinfo[t].number    = t
        tinfo[t].enumerate = enumer
        thread_create(ct.pointer(thread), init_and_exit,
                      ct.cast(ct.byref(tinfo[t]), ct.c_void_p))

    for t, thread in enumerate(threadId):
        thread_join(thread)
        if tinfo[t].err:
            errs += 1
            print("Thread {} failed (iteration {}): {}".format(
                  tinfo[t].number,
                  tinfo[t].iteration,
                  usb_error_name(tinfo[t].err)),
                  file=sys.stderr)
        elif enumer:
            if t > 0 and tinfo[t].devcount != last_devcount:
                devcount_mismatch += 1
                print("Device count mismatch: "
                      "Thread {} discovered {} devices instead of {}".format(
                      tinfo[t].number,
                      tinfo[t].devcount,
                      last_devcount))
            last_devcount = tinfo[t].devcount

    for no_acc in no_access:
        if no_acc.value:
            access_failures += 1

    if enumer and not devcount_mismatch:
        print("All threads discovered {} devices ({} not opened)".format(
              last_devcount, access_failures))

    return errs + devcount_mismatch


def main(argv=sys.argv[1:]):

    errs = 0

    print("Running multithreaded init/exit test...")
    errs += test_multi_init(0)
    print("Running multithreaded init/exit test with enumeration...")
    errs += test_multi_init(1)
    print("All done, {} errors".format(errs))

    return int(errs != 0)


if __name__.rpartition(".")[-1] == "__main__":
    sys.exit(main())
