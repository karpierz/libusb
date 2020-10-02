# Copyright (c) 2016-2020 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/licenses/Zlib

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

import sys
import ctypes as ct
import libusb as usb


def print_devs(devs):

    path = (ct.c_uint8 * 8)()

    i = 0
    while devs[i]:
        dev = devs[i]

        desc = usb.device_descriptor()
        r = usb.get_device_descriptor(dev, ct.byref(desc))
        if r < 0:
            print("failed to get device descriptor", file=sys.stderr)
            return

        print("{:04x}:{:04x} (bus {:d}, device {:d})".format(
              desc.idVendor, desc.idProduct,
              usb.get_bus_number(dev), usb.get_device_address(dev)), end="")

        r = usb.get_port_numbers(dev, path, ct.sizeof(path))
        if r > 0:
            print(" path: {:d}".format(path[0]), end="")
            for j in range(1, r):
                print(".{:d}".format(path[j]), end="")

        print()
        i += 1


def main(argv=sys.argv):

    r = usb.init(None)
    if r < 0:
        return r

    try:
        devs = ct.POINTER(ct.POINTER(usb.device))()
        cnt = usb.get_device_list(None, ct.byref(devs))
        if cnt < 0:
            return cnt

        print_devs(devs)

        usb.free_device_list(devs, 1)
    finally:
        usb.exit(None)

    return 0


sys.exit(main())
