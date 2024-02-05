# Copyright (c) 2016 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/license/zlib

# libusb example program to manipulate U.are.U 4000B fingerprint scanner.
# Copyright © 2007 Daniel Drake <dsd@gentoo.org>
# Copyright © 2016 Nathan Hjelm <hjelmn@mac.com>
# Copyright © 2020 Chris Dickens <christopher.a.dickens@gmail.com>
#
# Basic image capture program only, does not consider the powerup quirks or
# the fact that image encryption may be enabled. Not expected to work
# flawlessly all of the time.
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
import errno
import signal
import ctypes as ct

import libusb as usb
from libusb._platform import defined, is_posix, is_windows
if is_windows: import win32

usb_strerror = lambda r: usb.strerror(r).decode("utf-8")

if defined("DPFP_THREADED"):

    if is_posix:

        semaphore_t = ct.POINTER(sem_t)
        thread_t    = pthread_t
        thread_return_t = ct.c_void_p
        THREAD_RETURN_VALUE = NULL

        def semaphore_create() -> semaphore_t:
            name = "/org.libusb.example.dpfp_threaded:{:d}".format(int(getpid()))
            semaphore: semaphore_t = sem_open(name, O_CREAT | O_EXCL, 0, 0)
            if semaphore == SEM_FAILED:
                return NULL;
            # Remove semaphore so that it does not persist after process exits
            sem_unlink(name)
            return semaphore

        def semaphore_give(semaphore: semaphore_t):
            sem_post(semaphore)

        def semaphore_take(semaphore: semaphore_t):
            sem_wait(semaphore)

        def semaphore_destroy(semaphore: semaphore_t):
            sem_close(semaphore)

        # thread_return_t (*thread_entry)(arg: ct.c_void_p)
        def thread_create(thread: ct.POINTER(thread_t),
                          thread_entry,
                          arg: ct.c_void_p) -> int:
            r = pthread_create(thread, NULL, thread_entry, arg)
            return 0 if r == 0 else -1

        def thread_join(thread: thread_t):
            pthread_join(thread, NULL)

    elif is_windows:

        semaphore_t = win32.HANDLE
        thread_t    = win32.HANDLE
        if defined("__CYGWIN__"):
            thread_return_t = win32.DWORD
        else:
           #thread_return_t = ct.c_uint
            thread_return_t = win32.DWORD
        THREAD_RETURN_VALUE = 0

        def semaphore_create() -> semaphore_t:
            return win32.CreateSemaphore(None, 0, 1, None)

        def semaphore_give(semaphore: semaphore_t):
            win32.ReleaseSemaphore(semaphore, 1, None)

        def semaphore_take(semaphore: semaphore_t):
            win32.WaitForSingleObject(semaphore, win32.INFINITE)

        def semaphore_destroy(semaphore: semaphore_t):
            win32.CloseHandle(semaphore)

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

EP_INTR     = 1 | usb.LIBUSB_ENDPOINT_IN
EP_DATA     = 2 | usb.LIBUSB_ENDPOINT_IN
CTRL_IN     = usb.LIBUSB_REQUEST_TYPE_VENDOR | usb.LIBUSB_ENDPOINT_IN
CTRL_OUT    = usb.LIBUSB_REQUEST_TYPE_VENDOR | usb.LIBUSB_ENDPOINT_OUT
USB_RQ      = 0x04
INTR_LENGTH = 64

MODE_INIT             = 0x00
MODE_AWAIT_FINGER_ON  = 0x10
MODE_AWAIT_FINGER_OFF = 0x12
MODE_CAPTURE          = 0x20
MODE_SHUT_UP          = 0x30
MODE_READY            = 0x80

STATE_AWAIT_MODE_CHANGE_AWAIT_FINGER_ON  = 1
STATE_AWAIT_IRQ_FINGER_DETECTED          = 2
STATE_AWAIT_MODE_CHANGE_CAPTURE          = 3
STATE_AWAIT_IMAGE                        = 4
STATE_AWAIT_MODE_CHANGE_AWAIT_FINGER_OFF = 5
STATE_AWAIT_IRQ_FINGER_REMOVED           = 6

VID = 0x05ba
PID = 0x000a

state = 0  # int
devh  = ct.POINTER(usb.device_handle)()
imgbuf = (ct.c_ubyte * 0x1b340)()
irqbuf = (ct.c_ubyte * INTR_LENGTH)()
img_transfer = ct.POINTER(usb.transfer)()
irq_transfer = ct.POINTER(usb.transfer)()
img_idx = 0  # int
sig_atomic_t = int
do_exit = 0  # volatile sig_atomic_t
if defined("DPFP_THREADED"):
    exit_semaphore = semaphore_t()
    poll_thread    = thread_t()


#static
def request_exit(code: sig_atomic_t):

    global do_exit
    do_exit = code
    if defined("DPFP_THREADED"):
        semaphore_give(exit_semaphore)


if defined("DPFP_THREADED"):

    if is_posix:

        def poll_thread_main(arg: ct.c_void_p) -> thread_return_t:
            return _poll_thread_main(arg)

    elif is_windows:

        @win32.LPTHREAD_START_ROUTINE
        def poll_thread_main(arg: win32.LPVOID) -> thread_return_t:
            return _poll_thread_main(arg)

    def _poll_thread_main(arg):

        global do_exit

        print("poll thread running")

        while not do_exit:
            tv = usb.timeval(1, 0)
            r = usb.handle_events_timeout(None, ct.byref(tv))
            if r < 0:
                request_exit(2)
                break

        print("poll thread shutting down")
        return THREAD_RETURN_VALUE


def find_dpfp_device() -> int:

    global devh
    global VID, PID
    devh = usb.open_device_with_vid_pid(None, VID, PID)
    if not devh:
        ct.set_errno(errno.ENODEV)
        return -1
    return 0


def print_f0_data() ->int:

    global devh

    data = (ct.c_ubyte * 0x10)()
    r = usb.control_transfer(devh, CTRL_IN, USB_RQ, 0xf0, 0, data, ct.sizeof(data), 0)
    if r < 0:
        print("F0 error {}".format(r), file=sys.stderr)
        return r
    if r < ct.sizeof(data):
        print("short read ({})".format(r), file=sys.stderr)
        return -1

    print("F0 data:", end="")
    for i in range(ct.sizeof(data)):
        print(" {:02x}".format(data[i]), end="")
    print()
    return 0


#@annotate(status=ct.c_ubyte)
def get_hwstat(status) -> int:

    global devh

    r = usb.control_transfer(devh, CTRL_IN, USB_RQ, 0x07, 0, ct.byref(status), 1, 0)
    if r < 0:
        print("read hwstat error {}".format(r), file=sys.stderr)
        return r
    if r < 1:
        print("short read ({})".format(r), file=sys.stderr)
        return -1

    print("hwstat reads {:02x}".format(status))
    return 0


#@annotate(status=ct.c_ubyte)
def set_hwstat(status) -> int:

    global devh

    print("set hwstat to {:02x}".format(status))
    r = usb.control_transfer(devh, CTRL_OUT, USB_RQ, 0x07, 0, ct.byref(status), 1, 0)
    if r < 0:
        print("set hwstat error {}".format(r), file=sys.stderr)
        return r
    if r < 1:
        print("short write ({})".format(r), file=sys.stderr)
        return -1

    return 0


#@annotate(data=ct.c_ubyte)
def set_mode(data) -> int:

    global devh

    print("set mode {:02x}".format(data))
    r = usb.control_transfer(devh, CTRL_OUT, USB_RQ, 0x4e, 0, ct.byref(data), 1, 0)
    if r < 0:
        print("set mode error {}".format(r), file=sys.stderr)
        return r
    if r < 1:
        print("short write ({})".format(r), file=sys.stderr)
        return -1

    return 0


#static
@usb.transfer_cb_fn
def cb_mode_changed(transfer):

    if transfer.status != usb.LIBUSB_TRANSFER_COMPLETED:
        print("mode change transfer not completed!", file=sys.stderr)
        request_exit(2)

    print("async cb_mode_changed length={} actual_length={}".format(
          transfer.length, transfer.actual_length))
    if next_state() < 0:
        request_exit(2)


#static
#@annotate(data=ct.c_ubyte)
def set_mode_async(data) -> int:

    global devh

    try:
        buf = (ct.c_ubyte * (usb.LIBUSB_CONTROL_SETUP_SIZE + 1))()
    except:
        ct.set_errno(errno.ENOMEM)
        return -1

    transfer = usb.alloc_transfer(0)
    if not transfer:
        del buf
        ct.set_errno(errno.ENOMEM)
        return -1

    print("async set mode {:02x}".format(data))
    usb.fill_control_setup(buf, CTRL_OUT, USB_RQ, 0x4e, 0, 1)
    buf[usb.LIBUSB_CONTROL_SETUP_SIZE] = data
    usb.fill_control_transfer(transfer, devh, buf, cb_mode_changed, None, 1000)

    transfer.flags = (usb.LIBUSB_TRANSFER_SHORT_NOT_OK |
                      usb.LIBUSB_TRANSFER_FREE_BUFFER |
                      usb.LIBUSB_TRANSFER_FREE_TRANSFER)
    return usb.submit_transfer(transfer)


#@annotate(data=ct.POINTER(ct.c_ubyte))
def do_sync_intr(data) -> int:

    global devh

    transferred = ct.c_int()
    r = usb.interrupt_transfer(devh, EP_INTR, data, INTR_LENGTH, ct.byref(transferred), 1000)
    if r < 0:
        print("intr error {}".format(r), file=sys.stderr)
        return r
    if transferred < INTR_LENGTH:
        print("short read ({})".format(r), file=sys.stderr)
        return -1

    print("recv interrupt {:04x}".format(ct.cast(data, ct.POINTER(ct.c_uint16))[0]))
    return 0


#static
#@annotate(type=ct.c_ubyte)
def sync_intr(type) -> int:

    data = (ct.c_ubyte * INTR_LENGTH)()

    while True:
        r = do_sync_intr(data)
        if r < 0:
            return r
        if data[0] == type:
            return 0


#@annotate(data=ct.POINTER(ct.c_ubyte))
def save_to_file(data) -> int:

    global img_idx

    filename = "finger{}.pgm".format(img_idx)
    img_idx += 1
    try:
        f = open(filename, "w")
    except:
        return -1
    with f:
        f.write("P5 384 289 255 ")
        f.fwrite(data + 64, 384 * 289)
    print("saved image to {}".format(filename))
    return 0


#static
def next_state() -> int:

    global state

    print("old state: {}".format(state))

    r = 0
    if state == STATE_AWAIT_IRQ_FINGER_REMOVED:
        state = STATE_AWAIT_MODE_CHANGE_AWAIT_FINGER_ON
        r = set_mode_async(MODE_AWAIT_FINGER_ON)
    elif state == STATE_AWAIT_MODE_CHANGE_AWAIT_FINGER_ON:
        state = STATE_AWAIT_IRQ_FINGER_DETECTED
    elif state == STATE_AWAIT_IRQ_FINGER_DETECTED:
        state = STATE_AWAIT_MODE_CHANGE_CAPTURE
        r = set_mode_async(MODE_CAPTURE)
    elif state == STATE_AWAIT_MODE_CHANGE_CAPTURE:
        state = STATE_AWAIT_IMAGE
    elif state == STATE_AWAIT_IMAGE:
        state = STATE_AWAIT_MODE_CHANGE_AWAIT_FINGER_OFF
        r = set_mode_async(MODE_AWAIT_FINGER_OFF)
    elif state == STATE_AWAIT_MODE_CHANGE_AWAIT_FINGER_OFF:
        state = STATE_AWAIT_IRQ_FINGER_REMOVED
    else:
        print("unrecognised state {}".format(state))
    if r < 0:
        print("error detected changing state", file=sys.stderr)
        return r

    print("new state: {}".format(state))
    return 0


#static
@usb.transfer_cb_fn
def cb_irq(transfer):

    global state
    global irq_transfer

    irqtype = ct.cast(transfer.buffer[0], ct.c_ubyte)

    if transfer.status != usb.LIBUSB_TRANSFER_COMPLETED:
        print("irq transfer status {}?".format(transfer.status), file=sys.stderr)
        err_free_irq_transfer(transfer)

    print("IRQ callback {:02x}".format(irqtype))

    if state == STATE_AWAIT_IRQ_FINGER_DETECTED:
        if irqtype == 0x01:
            if next_state() < 0:
                err_free_irq_transfer(transfer)
        else:
            print("finger-on-sensor detected in wrong state!")
    elif state == STATE_AWAIT_IRQ_FINGER_REMOVED:
        if irqtype == 0x02:
            if next_state() < 0:
                err_free_irq_transfer(transfer)
        else:
            print("finger-on-sensor detected in wrong state!")

    if usb.submit_transfer(irq_transfer) < 0:
        err_free_irq_transfer(transfer)

def err_free_irq_transfer(transfer):
    global irq_transfer
    usb.free_transfer(transfer)
    irq_transfer = ct.POINTER(usb.transfer)()
    request_exit(2)


#static
@usb.transfer_cb_fn
def cb_img(transfer):

    global imgbuf
    global img_transfer

    if transfer.status != usb.LIBUSB_TRANSFER_COMPLETED:
        print("img transfer status {}?".format(transfer.status), file=sys.stderr)
        err_free_img_transfer(transfer)

    print("Image callback")
    save_to_file(imgbuf)
    if next_state() < 0:
        err_free_img_transfer(transfer)

    if usb.submit_transfer(img_transfer) < 0:
        err_free_img_transfer(transfer)

def err_free_img_transfer(transfer):
    global img_transfer
    usb.free_transfer(transfer)
    img_transfer = ct.POINTER(usb.transfer)()
    request_exit(2)


#static
def init_capture() -> int:

    global state
    global img_transfer
    global irq_transfer

    r = usb.submit_transfer(irq_transfer)
    if r < 0:
        return r

    r = usb.submit_transfer(img_transfer)
    if r < 0:
        usb.cancel_transfer(irq_transfer)
        while irq_transfer:
            if usb.handle_events(None) < 0:
                break
        return r

    # start state machine
    state = STATE_AWAIT_IRQ_FINGER_REMOVED
    return next_state()


#static
def do_init() -> int:

    status = ct.c_ubyte()
    r = get_hwstat(ct.byref(status))
    if r < 0:
        return r

    if not (status & 0x80):
        r = set_hwstat(status | 0x80)
        if r < 0:
            return r
        r = get_hwstat(ct.byref(status))
        if r < 0:
            return r

    status &= ~0x80
    r = set_hwstat(status)
    if r < 0:
        return r

    r = get_hwstat(ct.byref(status))
    if r < 0:
        return r

    r = sync_intr(0x56)
    if r < 0:
        return r

    return 0


#static
def alloc_transfers() -> int:

    global devh
    global imgbuf
    global irqbuf
    global img_transfer
    global irq_transfer

    img_transfer = usb.alloc_transfer(0)
    if not img_transfer:
        ct.set_errno(errno.ENOMEM)
        return -1

    irq_transfer = usb.alloc_transfer(0)
    if not irq_transfer:
        ct.set_errno(errno.ENOMEM)
        return -1

    usb.fill_bulk_transfer(img_transfer, devh, EP_DATA,
                           imgbuf, ct.sizeof(imgbuf),
                           cb_img, None, 0)
    usb.fill_interrupt_transfer(irq_transfer, devh, EP_INTR,
                                irqbuf, ct.sizeof(irqbuf),
                                cb_irq, None, 0)
    return 0


#static
def sighandler(signum, frame):
    request_exit(1)


#static
def setup_signals():
    if is_posix:
        sigact = struct_sigaction()
        sigact.sa_handler = sighandler
        sigemptyset(ct.byref(sigact.sa_mask))
        sigact.sa_flags = 0

        sigaction(signal.SIGINT,  ct.byref(sigact), NULL)
        sigaction(signal.SIGTERM, ct.byref(sigact), NULL)
        if hasattr(signal, "SIGQUIT"):
            sigaction(signal.SIGQUIT, ct.byref(sigact), NULL)
    else:
        signal(signal.SIGINT,  sighandler)
        signal(signal.SIGTERM, sighandler)


def main(argv=sys.argv[1:]):

    global devh
    global img_transfer
    global irq_transfer
    global do_exit

    r = (usb.init_context(None, None, 0)
         if hasattr(usb, "init_context") else
         usb.init(None))
    if r < 0:
        print("failed to initialise libusb {} - {}".format(r, usb_strerror(r)),
              file=sys.stderr)
        sys.exit(1)

    r = find_dpfp_device()
    try:
        if r < 0:
            print("Could not find/open device", file=sys.stderr)
            return abs(r)

        r = usb.claim_interface(devh, 0)
        if r < 0:
            print("claim interface error {} - {}".format(r, usb_strerror(r)),
                  file=sys.stderr)
            return abs(r)
        print("claimed interface")

        r = print_f0_data()
        if r < 0:
            usb.release_interface(devh, 0)
            return abs(r)

        r = do_init()
        try:
            if r < 0:
                return abs(r)

            # async from here onwards
            setup_signals()

            r = alloc_transfers()
            if r < 0:
                return abs(r)

            if defined("DPFP_THREADED"):

                exit_semaphore = semaphore_create()
                if not exit_semaphore:
                    print("failed to initialise semaphore", file=sys.stderr)
                    return abs(r)

                r = thread_create(ct.byref(poll_thread), poll_thread_main, ct.c_void_p(0))
                if r:
                    semaphore_destroy(exit_semaphore)
                    return abs(r)

                r = init_capture()
                if r < 0:
                    request_exit(2)

                while not do_exit:
                    semaphore_take(exit_semaphore)
            else:
                r = init_capture()
                if r < 0:
                    return abs(r)

                while not do_exit:
                    r = usb.handle_events(None)
                    if r < 0:
                        request_exit(2)

            print("shutting down...")

            if defined("DPFP_THREADED"):
                thread_join(poll_thread)
                semaphore_destroy(exit_semaphore)

            if img_transfer:
                r = usb.cancel_transfer(img_transfer)
                if r < 0:
                    print("failed to cancel transfer {} - {}".format(r, usb_strerror(r)),
                          file=sys.stderr)

            if irq_transfer:
                r = usb.cancel_transfer(irq_transfer)
                if r < 0:
                    print("failed to cancel transfer {} - {}".format(r, usb_strerror(r)),
                          file=sys.stderr)

            while img_transfer or irq_transfer:
                if usb.handle_events(None) < 0:
                    break

            r = 0 if do_exit == 1 else 1

        finally:
            if img_transfer: usb.free_transfer(img_transfer)
            if irq_transfer: usb.free_transfer(irq_transfer)
            set_mode(0)
            set_hwstat(0x80)
            usb.release_interface(devh, 0)
    finally:
        usb.close(devh)
        usb.exit(None)

    return abs(r)


if __name__.rpartition(".")[-1] == "__main__":
    sys.exit(main())
