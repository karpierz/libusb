# Copyright (c) 2016-2020 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/licenses/Zlib

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

verbose = False


def print_endpoint_comp(ep_comp):
    print("      USB 3.0 Endpoint Companion:")
    print("        bMaxBurst:        {:d}".format(ep_comp.bMaxBurst))
    print("        bmAttributes:     {:#04x}".format(ep_comp.bmAttributes))
    print("        wBytesPerInterval: {:d}".format(ep_comp.wBytesPerInterval))


def print_endpoint(endpoint):
    print("      Endpoint:")
    print("        bEndpointAddress: {:02x}".format(endpoint.bEndpointAddress))
    print("        bmAttributes:     {:02x}".format(endpoint.bmAttributes))
    print("        wMaxPacketSize:   {:d}".format(endpoint.wMaxPacketSize))
    print("        bInterval:        {:d}".format(endpoint.bInterval))
    print("        bRefresh:         {:d}".format(endpoint.bRefresh))
    print("        bSynchAddress:    {:d}".format(endpoint.bSynchAddress))
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
    print("      bInterfaceNumber:   {:d}".format(interface.bInterfaceNumber))
    print("      bAlternateSetting:  {:d}".format(interface.bAlternateSetting))
    print("      bNumEndpoints:      {:d}".format(interface.bNumEndpoints))
    print("      bInterfaceClass:    {:d}".format(interface.bInterfaceClass))
    print("      bInterfaceSubClass: {:d}".format(interface.bInterfaceSubClass))
    print("      bInterfaceProtocol: {:d}".format(interface.bInterfaceProtocol))
    print("      iInterface:         {:d}".format(interface.iInterface))
    for i in range(interface.bNumEndpoints):
        print_endpoint(interface.endpoint[i])


def print_2_0_ext_cap(usb_2_0_ext_cap):
    print("    USB 2.0 Extension Capabilities:")
    print("      bDevCapabilityType: {:d}".format(usb_2_0_ext_cap.bDevCapabilityType))
    print("      bmAttributes:       {:#x}".format(usb_2_0_ext_cap.bmAttributes))


def print_ss_usb_cap(ss_usb_cap):
    print("    USB 3.0 Capabilities:")
    print("      bDevCapabilityType: {:d}".format(ss_usb_cap.bDevCapabilityType))
    print("      bmAttributes:       {:#x}".format(ss_usb_cap.bmAttributes))
    print("      wSpeedSupported:    {:#x}".format(ss_usb_cap.wSpeedSupported))
    print("      bFunctionalitySupport: {:d}".format(ss_usb_cap.bFunctionalitySupport))
    print("      bU1devExitLat:      {:d}".format(ss_usb_cap.bU1DevExitLat))
    print("      bU2devExitLat:      {:d}".format(ss_usb_cap.bU2DevExitLat))


def print_bos(handle):

    bos = ct.POINTER(usb.bos_descriptor)()
    ret = usb.get_bos_descriptor(ct.byref(handle), ct.byref(bos))
    if ret < 0:
        return
    bos = bos[0]

    print("  Binary Object Store (BOS):")
    print("    wTotalLength:       {:d}".format(bos.wTotalLength))
    print("    bNumDeviceCaps:     {:d}".format(bos.bNumDeviceCaps))

    if bos.dev_capability[0][0].bDevCapabilityType == usb.LIBUSB_BT_USB_2_0_EXTENSION:
        usb_2_0_extension = ct.POINTER(usb.usb_2_0_extension_descriptor)()
        ret =  usb.get_usb_2_0_extension_descriptor(None, bos.dev_capability[0],
                                                    ct.byref(usb_2_0_extension))
        if ret < 0:
            return
        print_2_0_ext_cap(usb_2_0_extension[0])
        usb.free_usb_2_0_extension_descriptor(usb_2_0_extension)

    if bos.dev_capability[0][0].bDevCapabilityType == usb.LIBUSB_BT_SS_USB_DEVICE_CAPABILITY:
        dev_cap = ct.POINTER(usb.ss_usb_device_capability_descriptor)()
        ret = usb.get_ss_usb_device_capability_descriptor(None, bos.dev_capability[0],
                                                          ct.byref(dev_cap))
        if ret < 0:
            return
        print_ss_usb_cap(dev_cap[0])
        usb.free_ss_usb_device_capability_descriptor(dev_cap)

    usb.free_bos_descriptor(ct.byref(bos))


def print_interface(interface):
    for i in range(interface.num_altsetting):
        print_altsetting(interface.altsetting[i])


def print_configuration(config):
    print("  Configuration:")
    print("    wTotalLength:         {:d}".format(config.wTotalLength))
    print("    bNumInterfaces:       {:d}".format(config.bNumInterfaces))
    print("    bConfigurationValue:  {:d}".format(config.bConfigurationValue))
    print("    iConfiguration:       {:d}".format(config.iConfiguration))
    print("    bmAttributes:         {:02x}".format(config.bmAttributes))
    print("    MaxPower:             {:d}".format(config.MaxPower))
    for i in range(config.bNumInterfaces):
        print_interface(config.interface[i])


def print_device(device_p, level):

    global verbose

    string_descr = ct.create_string_buffer(256)

    desc = usb.device_descriptor()
    ret = usb.get_device_descriptor(device_p, ct.byref(desc))
    if ret < 0:
        print("failed to get device descriptor", file=sys.stderr)
        return -1

    handle = ct.POINTER(usb.device_handle)()
    ret = usb.open(device_p, ct.byref(handle))
    if ret == usb.LIBUSB_SUCCESS:

        if desc.iManufacturer:
            ret = usb.get_string_descriptor_ascii(handle, desc.iManufacturer,
                      ct.cast(string_descr, ct.POINTER(ct.c_ubyte)), ct.sizeof(string_descr))
            if ret > 0:
                description = "{!s} - ".format(string_descr.value.decode())
            else:
                description = "{:04X} - ".format(desc.idVendor)
        else:
            description = "{:04X} - ".format(desc.idVendor)

        if desc.iProduct:
            ret = usb.get_string_descriptor_ascii(handle, desc.iProduct,
                      ct.cast(string_descr, ct.POINTER(ct.c_ubyte)), ct.sizeof(string_descr))
            if ret > 0:
                description += "{!s}".format(string_descr.value.decode())
            else:
                description += "{:04X}".format(desc.idProduct)
        else:
            description += "{:04X}".format(desc.idProduct)
    else:
        description = "{:04X} - {:04X}".format(desc.idVendor, desc.idProduct)

    print("{:<{width}}Dev (bus {:d}, device {:d}): {}".format(" " * 20,
          usb.get_bus_number(device_p), usb.get_device_address(device_p), description,
          width=level * 2))

    if handle and verbose:
        if desc.iSerialNumber:
            ret = usb.get_string_descriptor_ascii(handle, desc.iSerialNumber,
                      ct.cast(string_descr, ct.POINTER(ct.c_ubyte)), ct.sizeof(string_descr))
            if ret > 0:
                print("{:<{width}}  - Serial Number: {!s}".format(" " * 20,
                                                                  string_descr.value.decode(),
                                                                  width=level * 2))
    if verbose:

        for i in range(desc.bNumConfigurations):
            config = ct.POINTER(usb.config_descriptor)()
            ret = usb.get_config_descriptor(device_p, i, ct.byref(config))
            if ret != usb.LIBUSB_SUCCESS:
                print("  Couldn't retrieve descriptors")
                continue
            print_configuration(config[0])
            usb.free_config_descriptor(config)

        if handle and desc.bcdUSB >= 0x0201:
            print_bos(handle[0])

    if handle:
        usb.close(handle)

    return 0


def main(argv=sys.argv):

    global verbose
    if len(argv) > 1 and argv[1] == "-v":
        verbose = True

    r = usb.init(None)
    if r < 0:
        return r

    try:
        devs = ct.POINTER(ct.POINTER(usb.device))()
        cnt = usb.get_device_list(None, ct.byref(devs))
        if cnt < 0:
            return cnt

        i = 0
        while devs[i]:
            print_device(devs[i], 0)
            i += 1

        usb.free_device_list(devs, 1)
    finally:
        usb.exit(None)

    return 0


sys.exit(main())
