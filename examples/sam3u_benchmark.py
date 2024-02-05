# Copyright (c) 2016 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/license/zlib

# libusb example program to measure Atmel SAM3U isochronous performance
# Copyright (C) 2012 Harald Welte <laforge@gnumonks.org>
#
# Copied with the author's permission under LGPL-2.1 from
# http://git.gnumonks.org/cgi-bin/gitweb.cgi?p=sam3u-tests.git;
#        a=blob;f=usb-benchmark-project/host/benchmark.c;
#        h=74959f7ee88f1597286cd435f312a8ff52c56b7e
#
# An Atmel SAM3U test firmware is also available in the above repository.
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
import signal
from datetime import datetime
import ctypes as ct

import libusb as usb
from libusb._platform import is_posix

usb_error_name = lambda status: usb.error_name(status).decode("utf-8")

EP_DATA_IN = 0x82
EP_ISO_IN  = 0x86

VID = 0x16c0
PID = 0x0763

devh     = None
tv_start = None

sig_atomic_t = int
do_exit   = 0  # volatile sig_atomic_t
num_bytes = 0
num_xfer  = 0

buf = (ct.c_uint8 * 2048)()


@usb.transfer_cb_fn
def cb_xfr(xfr):

    global num_bytes
    global num_xfer

    xfr = xfr[0]

    if xfr.status != usb.LIBUSB_TRANSFER_COMPLETED:
        print("transfer status {}".format(xfr.status), file=sys.stderr)
        usb.free_transfer(ct.byref(xfr))
        sys.exit(3)

    if xfr.type == usb.LIBUSB_TRANSFER_TYPE_ISOCHRONOUS:
        for i in range(xfr.num_iso_packets):
            pack = xfr.iso_packet_desc[i]
            if pack.status != usb.LIBUSB_TRANSFER_COMPLETED:
                print("Error: pack {} status {}".format(i, pack.status), file=sys.stderr)
                sys.exit(5)

            print("pack{} length:{}, actual_length:{}".format(
                  i, pack.length, pack.actual_length))

    print("length:{}, actual_length:{}".format(xfr.length, xfr.actual_length))
    for i in range(xfr.actual_length):
        print("{:02x}".format(xfr.buffer[i]), end="")
        if   i % 16: print()
        elif i % 8:  print("  ", end="")
        else:        print(" ",  end="")

    num_bytes += xfr.actual_length
    num_xfer  += 1

    rc = usb.submit_transfer(ct.byref(xfr))
    if rc < 0:
        print("error re-submitting URB", file=sys.stderr)
        sys.exit(1)


def benchmark_in(ep):

    global devh
    global tv_start
    global buf

    if ep == EP_ISO_IN:
        num_iso_pack = 16
    else:
        num_iso_pack = 0

    xfr = usb.alloc_transfer(num_iso_pack)
    if not xfr:
        ct.set_errno(errno.ENOMEM)
        return -1

    if ep == EP_ISO_IN:
        usb.fill_iso_transfer(xfr, devh, ep, buf, ct.sizeof(buf),
                              num_iso_pack, cb_xfr, None, 0)
        usb.set_iso_packet_lengths(xfr, ct.sizeof(buf) // num_iso_pack)
    else:
        usb.fill_bulk_transfer(xfr, devh, ep, buf, ct.sizeof(buf),
                               cb_xfr, None, 0)

    tv_start = datetime.now()

    # NOTE: To reach maximum possible performance the program must
    # submit *multiple* transfers here, not just one.
    #
    # When only one transfer is submitted there is a gap in the bus
    # schedule from when the transfer completes until a new transfer
    # is submitted by the callback. This causes some jitter for
    # isochronous transfers and loss of throughput for bulk transfers.
    #
    # This is avoided by queueing multiple transfers in advance, so
    # that the host controller is always kept busy, and will schedule
    # more transfers on the bus while the callback is running for
    # transfers which have completed on the bus.

    return usb.submit_transfer(xfr)


def measure():

    global num_bytes
    global num_xfer

    global tv_start
    tv_stop = datetime.now()

    diff_msec = int((tv_stop - tv_start).total_seconds() * 1000)

    print("{} transfers (total {} bytes) in {} milliseconds => {} bytes/sec".format(
          num_xfer, num_bytes, diff_msec, (num_bytes * 1000) // diff_msec))


def sig_hdlr(signum, frame):

    global do_exit

    measure()
    do_exit = 1


def main(argv=sys.argv[1:]):

    global devh
    global VID, PID
    global do_exit

    if is_posix:
        sigact = struct_sigaction()
        sigact.sa_handler = sig_hdlr
        sigemptyset(ct.byref(sigact.sa_mask))
        sigact.sa_flags = 0
        sigaction(signal.SIGINT, ct.byref(sigact), NULL)
    else:
        signal.signal(signal.SIGINT, sig_hdlr)

    rc = (usb.init_context(None, None, 0)
          if hasattr(usb, "init_context") else
          usb.init(None))
    if rc < 0:
        print("Error initializing libusb: {}".format(usb_error_name(rc)),
              file=sys.stderr)
        sys.exit(1)

    try:
        devh = usb.open_device_with_vid_pid(None, VID, PID)
        if not devh:
            print("Error finding USB device", file=sys.stderr)
            return rc

        rc = usb.claim_interface(devh, 2)
        if rc < 0:
            print("Error claiming interface: {}".format(usb_error_name(rc)),
                  file=sys.stderr)
            return rc

        benchmark_in(EP_ISO_IN)

        while not do_exit:
            rc = usb.handle_events(None)
            if rc != usb.LIBUSB_SUCCESS:
                break

        # Measurement has already been done by the signal handler.

        usb.release_interface(devh, 2)
    finally:
        if devh:
            usb.close(devh)
        usb.exit(None)

    return rc


if __name__.rpartition(".")[-1] == "__main__":
    sys.exit(main())
