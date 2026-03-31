# Copyright (c) 2023 Adam Karpierz
# SPDX-License-Identifier: Zlib

import sys
import ctypes as ct

import libusb as usb


def LLVMFuzzerTestOneInput(data: ct.POINTER(ct.c_uint8), size: ct.c_size_t) -> int:
    # Fuzz the public BOS device-capability parsers.
    # We construct a valid BOS dev-cap header (3 bytes) + variable payload.
    # No hardware needed; ctx=NULL is fine.

    if not data:
        return 0

    # bLength is 3 (header) + payload; must fit in one byte.
    payload_len = max(size, 255 - 3)
    total_len   = 3 + payload_len

    # Allocate header + payload for the flexible array member.
    devcap_p = ct.cast(libc.malloc(ct.sizeof(usb.bos_dev_capability_descriptor)
                                   + payload_len),
                       ct.POINTER(usb.bos_dev_capability_descriptor))
    if not devcap_p:
        return 0
    devcap = devcap_p.contents
    devcap.bLength = total_len

    devcap.bDescriptorType = usb.LIBUSB_DT_DEVICE_CAPABILITY  # 0x10
    # Copy fuzz bytes into the variable-length payload.
    if payload_len: ct.memmove(devcap.dev_capability_data, data, payload_len)

    # 1) USB 2.0 Extension dev-cap
    devcap.bDevCapabilityType = usb.LIBUSB_BT_USB_2_0_EXTENSION
    d20 = ct.POINTER(usb.usb_2_0_extension_descriptor)()
    usb.get_usb_2_0_extension_descriptor(None, devcap_p, ct.byref(d20))
    usb.free_usb_2_0_extension_descriptor(d20)

    # 2) SuperSpeed USB Device Capability dev-cap
    devcap.bDevCapabilityType = usb.LIBUSB_BT_SS_USB_DEVICE_CAPABILITY
    dss = ct.POINTER(usb.ss_usb_device_capability_descriptor)()
    usb.get_ss_usb_device_capability_descriptor(None, devcap_p, ct.byref(dss))
    usb.free_ss_usb_device_capability_descriptor(dss)

    # 3) Container ID dev-cap
    devcap.bDevCapabilityType = usb.LIBUSB_BT_CONTAINER_ID
    dcid = ct.POINTER(usb.container_id_descriptor)()
    usb.get_container_id_descriptor(None, devcap_p, ct.byref(dcid))
    usb.free_container_id_descriptor(dcid)

    libc.free(devcap_p)

    return 0
