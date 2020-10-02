# Copyright (c) 2016-2020 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/licenses/Zlib

# libusb example program to manipulate U.are.U 4000B fingerprint scanner.
# Copyright © 2007 Daniel Drake <dsd@gentoo.org>
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
do_exit = 0  # int


#static
#@annotate(code=int)
def request_exit(code):

    global do_exit
    do_exit = code


#@annotate(int)
def find_dpfp_device():

    global devh
    global VID, PID
    devh = usb.open_device_with_vid_pid(None, VID, PID)
    return 0 if devh else -errno.EIO


#@annotate(int)
def print_f0_data():

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
        print("{:02x} ".format(data[i]), end="")
    print()
    return 0


#@annotate(int, status=ct.c_ubyte)
def get_hwstat(status):

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


#@annotate(int, status=ct.c_ubyte)
def set_hwstat(status):

    global devh

    print("set hwstat to {:02x}".format(status))

    r = usb.control_transfer(devh, CTRL_OUT, USB_RQ, 0x07, 0, ct.byref(status), 1, 0)
    if r < 0:
        print("set hwstat error {}".format(r), file=sys.stderr)
        return r
    if r < 1:
        print("short write ({})".format(r), file=sys.stderr, end="")
        return -1

    return 0


#@annotate(int, data=ct.c_ubyte)
def set_mode(data):

    global devh

    print("set mode {:02x}".format(data))

    r = usb.control_transfer(devh, CTRL_OUT, USB_RQ, 0x4e, 0, ct.byref(data), 1, 0)
    if r < 0:
        print("set mode error {}".format(r), file=sys.stderr)
        return r
    if r < 1:
        print("short write ({})".format(r), file=sys.stderr, end="")
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
#@annotate(int, data=ct.c_ubyte)
def set_mode_async(data):

    global devh

    buf = ct.cast(malloc(usb.LIBUSB_CONTROL_SETUP_SIZE + 1), ct.POINTER(ct.c_ubyte))
    if not buf:
        return -errno.ENOMEM

    transfer = usb.alloc_transfer(0)  # ct.POINTER(usb.transfer)
    if not transfer:
        free(buf);
        return -errno.ENOMEM

    print("async set mode {:02x}".format(data))
    usb.fill_control_setup(buf, CTRL_OUT, USB_RQ, 0x4e, 0, 1)
    buf[usb.LIBUSB_CONTROL_SETUP_SIZE] = data
    usb.fill_control_transfer(transfer, devh, buf, cb_mode_changed, None, 1000)

    transfer.flags = (usb.LIBUSB_TRANSFER_SHORT_NOT_OK |
                      usb.LIBUSB_TRANSFER_FREE_BUFFER |
                      usb.LIBUSB_TRANSFER_FREE_TRANSFER)
    return usb.submit_transfer(transfer)


#@annotate(data=ct.POINTER(ct.c_ubyte))
def do_sync_intr(data):

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
#@annotate(int, type=ct.c_ubyte)
def sync_intr(type):

    data = (ct.c_ubyte * INTR_LENGTH)()

    while True:
        r = do_sync_intr(data)
        if r < 0:
            return r
        if data[0] == type:
            return 0


#@annotate(data=ct.POINTER(ct.c_ubyte))
def save_to_file(data):

    global img_idx

    filename = "finger{}.pgm".format(img_idx)
    img_idx += 1
    try:
        fd = open(filename, "w")
    except:
        return -1
    with fd:
        fd.write("P5 384 289 255 ")
        fd.fwrite(data + 64, 384 * 289)
    print("saved image to {}".format(filename))
    return 0


#static
#@annotate(int)
def next_state():

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
        request_exit(2)
        usb.free_transfer(transfer)
        irq_transfer = ct.POINTER(usb.transfer)()
        return

    print("IRQ callback {:02x}".format(irqtype))

    if state == STATE_AWAIT_IRQ_FINGER_DETECTED:
        if irqtype == 0x01:
            if next_state() < 0:
                request_exit(2)
                return
        else:
            print("finger-on-sensor detected in wrong state!")
    elif state == STATE_AWAIT_IRQ_FINGER_REMOVED:
        if irqtype == 0x02:
            if next_state() < 0:
                request_exit(2)
                return
        else:
            print("finger-on-sensor detected in wrong state!")

    if usb.submit_transfer(irq_transfer) < 0:
        request_exit(2)


#static
@usb.transfer_cb_fn
def cb_img(transfer):

    global imgbuf
    global img_transfer

    if transfer.status != usb.LIBUSB_TRANSFER_COMPLETED:
        print("img transfer status {}?".format(transfer.status), file=sys.stderr)
        request_exit(2)
        usb.free_transfer(transfer)
        img_transfer = ct.POINTER(usb.transfer)()
        return

    print("Image callback")
    save_to_file(imgbuf)
    if next_state() < 0:
        request_exit(2)
        return

    if usb.submit_transfer(img_transfer) < 0:
        request_exit(2)


#static
#@annotate(int)
def init_capture():

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
#@annotate(int)
def do_init():

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
#@annotate(int)
def alloc_transfers():

    global devh
    global imgbuf
    global irqbuf
    global img_transfer
    global irq_transfer

    img_transfer = usb.alloc_transfer(0)
    if not img_transfer:
        return -errno.ENOMEM

    irq_transfer = usb.alloc_transfer(0)
    if not irq_transfer:
        return -errno.ENOMEM

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


def main(argv=sys.argv):

    global devh
    global img_transfer
    global irq_transfer
    global do_exit

    r = usb.init(None)
    if r < 0:
        print("failed to initialise libusb", file=sys.stderr)
        sys.exit(1)

    r = find_dpfp_device()
    try:
        if r < 0:
            print("Could not find/open device", file=sys.stderr)
            return abs(r)

        r = usb.claim_interface(devh, 0)
        if r < 0:
            print("usb_claim_interface error {}".format(r), file=sys.stderr)
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

            r = alloc_transfers()
            if r < 0:
                return abs(r)

            r = init_capture()
            if r < 0:
                return abs(r)

            #sigact = struct_sigaction()
            #sigact.sa_handler = sighandler
            #sigemptyset(ct.byref(sigact.sa_mask))
            #sigact.sa_flags = 0
            signal.signal(signal.SIGINT,  sighandler)
            signal.signal(signal.SIGTERM, sighandler)
            if hasattr(signal, "SIGQUIT"):
                signal.signal(signal.SIGQUIT, sighandler)

            while not do_exit:
                r = usb.handle_events(None)
                if r < 0:
                    return abs(r)

            print("shutting down...")

            if irq_transfer:
                r = usb.cancel_transfer(irq_transfer)
                if r < 0:
                    return abs(r)

            if img_transfer:
                r = usb.cancel_transfer(img_transfer)
                if r < 0:
                    return abs(r)

            while irq_transfer or img_transfer:
                if usb.handle_events(None) < 0:
                    break

            r = 0 if do_exit == 1 else 1

        finally:
            usb.free_transfer(img_transfer)
            usb.free_transfer(irq_transfer)
            set_mode(0);
            set_hwstat(0x80)
            usb.release_interface(devh, 0)
    finally:
        usb.close(devh)
        usb.exit(None)

    return abs(r)


sys.exit(main())
