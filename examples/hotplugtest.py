# Copyright (c) 2016 Adam Karpierz
# SPDX-License-Identifier: Zlib

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
from libusb._platform import is_windows

handle = ct.POINTER(usb.device_handle)()
done_attach = 0
done_detach = 0


@usb.hotplug_callback_fn
def hotplug_callback(ctx, dev, event, user_data):

    global handle, done_attach

    desc = usb.device_descriptor()
    new_handle = ct.POINTER(usb.device_handle)()

    rc = usb.get_device_descriptor(dev, ct.byref(desc))
    if rc == usb.LIBUSB_SUCCESS:
        print("Device attached: {:04x}:{:04x}".format(desc.idVendor, desc.idProduct))
    else:
        print("Device attached")
        print("Error getting device descriptor: {}".format(usb.strerror(rc).decode()),
              file=sys.stderr)

    rc = usb.open(dev, ct.byref(new_handle))
    if rc == usb.LIBUSB_SUCCESS:
        if handle:
            usb.close(handle)
        handle = new_handle
    elif (rc != usb.LIBUSB_ERROR_ACCESS
          and (not is_windows
               or rc not in (usb.LIBUSB_ERROR_NOT_SUPPORTED,
                             usb.LIBUSB_ERROR_NOT_FOUND))):
        print("No access to device: {}".format(usb.strerror(rc).decode()),
              file=sys.stderr)

    done_attach += 1

    return 0


@usb.hotplug_callback_fn
def hotplug_callback_detach(ctx, dev, event, user_data):

    global handle, done_detach

    desc = usb.device_descriptor()
    rc = usb.get_device_descriptor(dev, ct.byref(desc))
    if rc == usb.LIBUSB_SUCCESS:
        print("Device detached: {:04x}:{:04x}".format(desc.idVendor, desc.idProduct))
    else:
        print("Device detached")
        print("Error getting device descriptor: {}".format(usb.strerror(rc).decode()),
              file=sys.stderr)

    if handle:
        usb.close(handle)
        handle = ct.POINTER(usb.device_handle)()

    done_detach += 1

    return 0


def main(argv=sys.argv[1:]):

    global handle, done_attach, done_detach

    hp = [usb.hotplug_callback_handle() for i in range(2)]

    vendor_id  = int(argv[0]) if len(argv) > 0 else usb.LIBUSB_HOTPLUG_MATCH_ANY
    product_id = int(argv[1]) if len(argv) > 1 else usb.LIBUSB_HOTPLUG_MATCH_ANY
    class_id   = int(argv[2]) if len(argv) > 2 else usb.LIBUSB_HOTPLUG_MATCH_ANY

    rc = (usb.init_context(None, None, 0)
          if hasattr(usb, "init_context") else
          usb.init(None))
    if rc != usb.LIBUSB_SUCCESS:
        print("failed to initialise libusb: {}".format(usb.strerror(rc).decode()))
        return 1

    try:
        if not usb.has_capability(usb.LIBUSB_CAP_HAS_HOTPLUG):
            print("Hotplug capabilities are not supported on this platform")
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

        while done_detach < done_attach or done_attach == 0:
            rc = usb.handle_events(None)
            if rc != usb.LIBUSB_SUCCESS:
                print("libusb.handle_events() failed: {}".format(usb.strerror(rc).decode()))
    finally:
        if handle:
            print("Warning: Closing left-over open handle")
            usb.close(handle)
        usb.exit(None)

    return 0


if __name__.rpartition(".")[-1] == "__main__":
    sys.exit(main())
