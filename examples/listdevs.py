# coding: utf-8

# libusb example program to list devices on the bus
# Copyright © 2007 Daniel Drake <dsd@gentoo.org>
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

from __future__ import absolute_import, division, print_function

import sys
import ctypes as ct
import libusb as usb


def print_devs(devs):

    path = (ct.c_uint8, 8)()

    i = -1
    while True:
        i += 1
        device_p = devs[i]
        if not device_p: break

        desc = usb.device_descriptor()
        r = usb.get_device_descriptor(device_p, ct.byref(desc))
        if r < 0:
            print("failed to get device descriptor", file=sys.stderr)
            return

        print("{:04x}:{:04x} (bus {}, device {})".format(
              desc.idVendor, desc.idProduct,
              usb.get_bus_number(device_p), usb.get_device_address(device_p)), end="")

        r = usb.get_port_numbers(device_p, path, ct.sizeof(path))
        if r > 0:
            print(" path: {}".format(path[0]), end="")
            for j in range(1, r):
                print(".{}".format(path[j]), end="")

        print()


def main():

    r = usb.init(None)
    if r < 0: return r

    devs = ct.POINTER(ct.POINTER(usb.device))()
    cnt = usb.get_device_list(None, ct.byref(devs))
    if cnt < 0: return cnt

    print_devs(devs)

    usb.free_device_list(devs, 1)

    usb.exit(None)
    return 0


sys.exit(main() or 0)
