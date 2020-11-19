# Copyright (c) 2016-2020 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/licenses/Zlib

# libusb example program for hotplug API
# Copyright © 2012-2013 Nathan Hjelm <hjelmn@mac.com>
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


handle = ct.POINTER(usb.device_handle)()
done = 0


@usb.hotplug_callback_fn
def hotplug_callback(ctx, dev, event, user_data):

    global handle, done

    desc = usb.device_descriptor()
    rc = usb.get_device_descriptor(dev, ct.byref(desc))
    if rc != usb.LIBUSB_SUCCESS:
        print("Error getting device descriptor", file=sys.stderr)

    print("Device attached: {:04x}:{:04x}".format(desc.idVendor, desc.idProduct))

    if handle:
        usb.close(handle)
        handle = ct.POINTER(usb.device_handle)()

    rc = usb.open(dev, ct.byref(handle))
    if rc != usb.LIBUSB_SUCCESS:
        print("Error opening device", file=sys.stderr)

    done += 1

    return 0


@usb.hotplug_callback_fn
def hotplug_callback_detach(ctx, dev, event, user_data):

    global handle, done

    print("Device detached")

    if handle:
        usb.close(handle)
        handle = ct.POINTER(usb.device_handle)()

    done += 1

    return 0


def main(argv=sys.argv):

    global handle, done

    hp = [usb.hotplug_callback_handle() for i in range(2)]

    vendor_id  = int(argv[1]) if len(argv) > 1 else 0x045a
    product_id = int(argv[2]) if len(argv) > 2 else 0x5005
    class_id   = int(argv[3]) if len(argv) > 3 else usb.LIBUSB_HOTPLUG_MATCH_ANY

    rc = usb.init(None)
    if rc < 0:
        print("failed to initialise libusb: {}".format(usb.error_name(rc)))
        return 1

    try:
        if not usb.has_capability(usb.LIBUSB_CAP_HAS_HOTPLUG):
            print("Hotplug capabilites are not supported on this platform")
            return 1

        rc = usb.hotplug_register_callback(None,
                                           usb.LIBUSB_HOTPLUG_EVENT_DEVICE_ARRIVED, 0,
                                           vendor_id, product_id, class_id,
                                           hotplug_callback, None, ct.byref(hp[0]))
        if rc != usb.LIBUSB_SUCCESS:
            print("Error registering callback 0", file=sys.stderr)
            return 1

        rc = usb.hotplug_register_callback(None,
                                           usb.LIBUSB_HOTPLUG_EVENT_DEVICE_LEFT, 0,
                                           vendor_id, product_id, class_id,
                                           hotplug_callback_detach, None, ct.byref(hp[1]))
        if rc != usb.LIBUSB_SUCCESS:
            print("Error registering callback 1", file=sys.stderr)
            return 1

        while done < 2:
            rc = usb.handle_events(None)
            if rc < 0:
                print("libusb.handle_events() failed: {}".format(usb.error_name(rc)))
    finally:
        if handle:
            usb.close(handle)
        usb.exit(None)

    return 0


sys.exit(main())
