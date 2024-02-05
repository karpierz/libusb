# Copyright (c) 2016 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/license/zlib

# Test suite program based of libusb-0.1-compat testlibusb
# Copyright (c) 2013 Nathan Hjelm <hjelmn@mac.ccom>
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
from libusb._platform import is_linux

usb_strerror = lambda r: usb.strerror(r).decode("utf-8")

verbose = False


def print_endpoint_comp(ep_comp):
    print("      USB 3.0 Endpoint Companion:")
    print("        bMaxBurst:           {:d}".format(ep_comp.bMaxBurst))
    print("        bmAttributes:        {:02x}h".format(ep_comp.bmAttributes))
    print("        wBytesPerInterval:   {:d}".format(ep_comp.wBytesPerInterval))


def print_endpoint(endpoint):
    print("      Endpoint:")
    print("        bEndpointAddress:    {:02x}h".format(endpoint.bEndpointAddress))
    print("        bmAttributes:        {:02x}h".format(endpoint.bmAttributes))
    print("        wMaxPacketSize:      {:d}".format(endpoint.wMaxPacketSize))
    print("        bInterval:           {:d}".format(endpoint.bInterval))
    print("        bRefresh:            {:d}".format(endpoint.bRefresh))
    print("        bSynchAddress:       {:d}".format(endpoint.bSynchAddress))
    i = 0
    while i < endpoint.extra_length:
        if endpoint.extra[i + 1] == usb.LIBUSB_DT_SS_ENDPOINT_COMPANION:
            ep_comp = ct.POINTER(usb.ss_endpoint_companion_descriptor)()
            ret = usb.get_ss_endpoint_companion_descriptor(None, ct.byref(endpoint),
                                                           ct.byref(ep_comp))
            if ret != usb.LIBUSB_SUCCESS:
                continue
            print_endpoint_comp(ep_comp[0])
            usb.free_ss_endpoint_companion_descriptor(ep_comp)
        i += endpoint.extra[i]


def print_altsetting(interface):
    print("    Interface:")
    print("      bInterfaceNumber:      {:d}".format(interface.bInterfaceNumber))
    print("      bAlternateSetting:     {:d}".format(interface.bAlternateSetting))
    print("      bNumEndpoints:         {:d}".format(interface.bNumEndpoints))
    print("      bInterfaceClass:       {:d}".format(interface.bInterfaceClass))
    print("      bInterfaceSubClass:    {:d}".format(interface.bInterfaceSubClass))
    print("      bInterfaceProtocol:    {:d}".format(interface.bInterfaceProtocol))
    print("      iInterface:            {:d}".format(interface.iInterface))
    for i in range(interface.bNumEndpoints):
        print_endpoint(interface.endpoint[i])


def print_2_0_ext_cap(usb_2_0_ext_cap):
    print("    USB 2.0 Extension Capabilities:")
    print("      bDevCapabilityType:    {:d}".format(usb_2_0_ext_cap.bDevCapabilityType))
    print("      bmAttributes:          {:08x}h".format(usb_2_0_ext_cap.bmAttributes))


def print_ss_usb_cap(ss_usb_cap: usb.ss_usb_device_capability_descriptor):
    print("    USB 3.0 Capabilities:")
    print("      bDevCapabilityType:    {:d}".format(ss_usb_cap.bDevCapabilityType))
    print("      bmAttributes:          {:02x}h".format(ss_usb_cap.bmAttributes))
    print("      wSpeedSupported:       {:d}".format(ss_usb_cap.wSpeedSupported))
    print("      bFunctionalitySupport: {:d}".format(ss_usb_cap.bFunctionalitySupport))
    print("      bU1devExitLat:         {:d}".format(ss_usb_cap.bU1DevExitLat))
    print("      bU2devExitLat:         {:d}".format(ss_usb_cap.bU2DevExitLat))


def print_bos(handle: ct.POINTER(usb.device_handle)):

    bos = ct.POINTER(usb.bos_descriptor)()
    ret = usb.get_bos_descriptor(handle, ct.byref(bos))
    if ret < 0:
        return
    bos = bos[0]

    print("  Binary Object Store (BOS):")
    print("    wTotalLength:            {:d}".format(bos.wTotalLength))
    print("    bNumDeviceCaps:          {:d}".format(bos.bNumDeviceCaps))

    for i in range(bos.bNumDeviceCaps):
        dev_cap: ct.POINTER(usb.bos_dev_capability_descriptor) = bos.dev_capability[i]

        if dev_cap[0].bDevCapabilityType == usb.LIBUSB_BT_USB_2_0_EXTENSION:

            usb_2_0_extension = ct.POINTER(usb.usb_2_0_extension_descriptor)()
            ret = usb.get_usb_2_0_extension_descriptor(None, dev_cap,
                                                       ct.byref(usb_2_0_extension))
            if ret < 0:
                return

            print_2_0_ext_cap(usb_2_0_extension[0])
            usb.free_usb_2_0_extension_descriptor(usb_2_0_extension)

        elif dev_cap[0].bDevCapabilityType == usb.LIBUSB_BT_SS_USB_DEVICE_CAPABILITY:

            ss_dev_cap = ct.POINTER(usb.ss_usb_device_capability_descriptor)()
            ret = usb.get_ss_usb_device_capability_descriptor(None, dev_cap,
                                                              ct.byref(ss_dev_cap))
            if ret < 0:
                return

            print_ss_usb_cap(ss_dev_cap[0])
            usb.free_ss_usb_device_capability_descriptor(ss_dev_cap)

    usb.free_bos_descriptor(ct.byref(bos))


def print_interface(interface):
    for i in range(interface.num_altsetting):
        print_altsetting(interface.altsetting[i])


def print_configuration(config: usb.config_descriptor):
    print("  Configuration:")
    print("    wTotalLength:            {:d}".format(config.wTotalLength))
    print("    bNumInterfaces:          {:d}".format(config.bNumInterfaces))
    print("    bConfigurationValue:     {:d}".format(config.bConfigurationValue))
    print("    iConfiguration:          {:d}".format(config.iConfiguration))
    print("    bmAttributes:            {:02x}h".format(config.bmAttributes))
    print("    MaxPower:                {:d}".format(config.MaxPower))
    for i in range(config.bNumInterfaces):
        print_interface(config.interface[i])


def print_device(dev: ct.POINTER(usb.device), handle: ct.POINTER(usb.device_handle)):

    global verbose

    string_descr = ct.create_string_buffer(256)

    device_speed = usb.get_device_speed(dev)
    if   device_speed == usb.LIBUSB_SPEED_LOW:        speed = "1.5M"
    elif device_speed == usb.LIBUSB_SPEED_FULL:       speed = "12M"
    elif device_speed == usb.LIBUSB_SPEED_HIGH:       speed = "480M"
    elif device_speed == usb.LIBUSB_SPEED_SUPER:      speed = "5G"
    elif device_speed == usb.LIBUSB_SPEED_SUPER_PLUS: speed = "10G"
    else:                                             speed = "Unknown"

    desc = usb.device_descriptor()
    ret = usb.get_device_descriptor(dev, ct.byref(desc))
    if ret < 0:
        print("failed to get device descriptor", file=sys.stderr)
        return

    print("Dev (bus {}, device {}): {:04X} - {:04X} speed: {}".format(
           usb.get_bus_number(dev), usb.get_device_address(dev),
           desc.idVendor, desc.idProduct, speed))

    if not handle:
        handle = ct.POINTER(usb.device_handle)()
        usb.open(dev, ct.byref(handle))

    if handle:
        if desc.iManufacturer:
            ret = usb.get_string_descriptor_ascii(handle, desc.iManufacturer,
                      ct.cast(string_descr, ct.POINTER(ct.c_ubyte)), ct.sizeof(string_descr))
            if ret > 0:
                print("  Manufacturer:              {}".format(string_descr.value.decode()))

        if desc.iProduct:
            ret = usb.get_string_descriptor_ascii(handle, desc.iProduct,
                      ct.cast(string_descr, ct.POINTER(ct.c_ubyte)), ct.sizeof(string_descr))
            if ret > 0:
                print("  Product:                   {}".format(string_descr.value.decode()))

        if verbose and desc.iSerialNumber:
            ret = usb.get_string_descriptor_ascii(handle, desc.iSerialNumber,
                      ct.cast(string_descr, ct.POINTER(ct.c_ubyte)), ct.sizeof(string_descr))
            if ret > 0:
                print("  Serial Number:             {}".format(string_descr.value.decode()))

    if verbose:
        for i in range(desc.bNumConfigurations):
            config = ct.POINTER(usb.config_descriptor)()
            ret = usb.get_config_descriptor(dev, i, ct.byref(config))
            if ret != usb.LIBUSB_SUCCESS:
                print("  Couldn't retrieve descriptors")
                continue
            print_configuration(config[0])
            usb.free_config_descriptor(config)

        if handle and desc.bcdUSB >= 0x0201:
            print_bos(handle)

    if handle:
        usb.close(handle)


def test_wrapped_device(device_name: str) -> int:
    if is_linux:
        try:
            fd = os.open(device_name, os.O_RDWR)
        except OSError as exc:
            print("Error could not open {}: {}".format(device_name, strerror(exc.errno)))
            return 1

        handle = ct.POINTER(usb.device_handle)()
        r = usb.wrap_sys_device(None, fd, ct.byref(handle))
        if r:
            print("Error wrapping device: {}: {}".format(device_name, usb_strerror(r)))
            os.close(fd)
            return 1

        print_device(usb.get_device(handle), handle)
        os.close(fd)

        return 0
    else:
        print("Testing wrapped devices is not supported on your platform")
        return 1


def main(argv=sys.argv[1:]):

    global verbose

    device_name = None
    i = 0
    while i < len(argv):
        if argv[i] == "-v":
            verbose = True
        elif argv[i] == "-d" and (i + 1) < len(argv):
            i += 1
            device_name = argv[i]
        else:
            print("Usage {} [-v] [-d </dev/bus/usb/...>]".format(sys.argv[0]))
            print("Note use -d to test libusb.wrap_sys_device()")
            return 1
        i += 1

    r = (usb.init_context(None, None, 0)
         if hasattr(usb, "init_context") else
         usb.init(None))
    if r < 0:
        return r

    try:
        if device_name:
            r = test_wrapped_device(device_name)
        else:
            devs = ct.POINTER(ct.POINTER(usb.device))()
            cnt = usb.get_device_list(None, ct.byref(devs))
            if cnt < 0:
                return 1

            i = 0
            while devs[i]:
                print_device(devs[i], None)
                i += 1

            usb.free_device_list(devs, 1)
    finally:
        usb.exit(None)

    return r


if __name__.rpartition(".")[-1] == "__main__":
    sys.exit(main())
