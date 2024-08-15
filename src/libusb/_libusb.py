# Copyright (c) 2016 Adam Karpierz
# SPDX-License-Identifier: Zlib

# Public libusb header file
# Copyright (c) 2001 Johannes Erdfelt <johannes@erdfelt.com>
# Copyright (c) 2007-2008 Daniel Drake <dsd@gentoo.org>
# Copyright (c) 2012 Pete Batard <pete@akeo.ie>
# Copyright (c) 2012-2023 Nathan Hjelm <hjelmn@cs.unm.edu>
# Copyright (c) 2014-2020 Chris Dickens <christopher.a.dickens@gmail.com>
# For more information, please visit: https://libusb.info
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

import ctypes as ct

from ._platform import CFUNC
from ._platform import timeval
from ._platform import defined
from ._dll      import dll

intptr_t = (ct.c_int32 if ct.sizeof(ct.c_void_p) == ct.sizeof(ct.c_int32) else ct.c_int64)

# include <limits.h>
UINT_MAX = ct.c_uint(-1).value
INT_MAX  = UINT_MAX >> 1

def LIBUSB_DEPRECATED_FOR(f): pass

# \def LIBUSB_CALL
# \ingroup libusb::misc
# libusb's Windows calling convention.
#
# Under Windows, the selection of available compilers and configurations
# means that, unlike other platforms, there is not <em>one true calling
# convention</em> (calling convention: the manner in which parameters are
# passed to functions in the generated assembly code).
#
# Matching the Windows API itself, libusb uses the WINAPI convention (which
# translates to the <tt>stdcall</tt> convention) and guarantees that the
# library is compiled in this way. The public header file also includes
# appropriate annotations so that your own software will use the right
# convention, even if another convention is being used by default within
# your codebase.
#
# The one consideration that you must apply in your software is to mark
# all functions which you use as libusb callbacks with this LIBUSB_CALL
# annotation, so that they too get compiled for the correct calling
# convention.
#
# On non-Windows operating systems, this macro is defined as nothing. This
# means that you can apply it to your code without worrying about
# cross-platform compatibility.

# LIBUSB_CALL must be defined on both definition and declaration of libusb
# functions. You'd think that declaration would be enough, but cygwin will
# complain about conflicting types unless both are marked this way.
# The placement of this macro is important too; it must appear after the
# return type, before the function name. See internal documentation for
# API_EXPORTED.

# if defined(_WIN32) || defined(__CYGWIN__)
# define LIBUSB_CALL WINAPI
# define LIBUSB_CALLV WINAPIV
# else
# define LIBUSB_CALL
# define LIBUSB_CALLV
# endif /* _WIN32 || __CYGWIN__ */

# \def LIBUSB_API_VERSION
# \ingroup libusb::misc
# libusb's API version.
#
# Since version 1.0.18, to help with feature detection, libusb defines
# a LIBUSB_API_VERSION macro that gets increased every time there is a
# significant change to the API, such as the introduction of a new call,
# the definition of a new macro/enum member, or any other element that
# libusb applications may want to detect at compilation time.
#
# Between versions 1.0.13 and 1.0.17 (inclusive) the older spelling of
# LIBUSBX_API_VERSION was used.
#
# The macro is typically used in an application as follows:
# \code
# #if defined(LIBUSB_API_VERSION) && (LIBUSB_API_VERSION >= 0x01001234)
# // Use one of the newer features from the libusb API
# #endif
# \endcode
#
# Internally, LIBUSB_API_VERSION is defined as follows:
# (libusb major << 24) | (libusb minor << 16) | (16 bit incremental)
#
# The incremental component has changed as follows:
# <ul>
# <li>libusbx version 1.0.13: LIBUSBX_API_VERSION = 0x01000100
# <li>libusbx version 1.0.14: LIBUSBX_API_VERSION = 0x010000FF
# <li>libusbx version 1.0.15: LIBUSBX_API_VERSION = 0x01000101
# <li>libusbx version 1.0.16: LIBUSBX_API_VERSION = 0x01000102
# <li>libusbx version 1.0.17: LIBUSBX_API_VERSION = 0x01000102
# <li>libusb version 1.0.18: LIBUSB_API_VERSION = 0x01000102
# <li>libusb version 1.0.19: LIBUSB_API_VERSION = 0x01000103
# <li>libusb version 1.0.20: LIBUSB_API_VERSION = 0x01000104
# <li>libusb version 1.0.21: LIBUSB_API_VERSION = 0x01000105
# <li>libusb version 1.0.22: LIBUSB_API_VERSION = 0x01000106
# <li>libusb version 1.0.23: LIBUSB_API_VERSION = 0x01000107
# <li>libusb version 1.0.24: LIBUSB_API_VERSION = 0x01000108
# <li>libusb version 1.0.25: LIBUSB_API_VERSION = 0x01000109
# <li>libusb version 1.0.26: LIBUSB_API_VERSION = 0x01000109
# <li>libusb version 1.0.27: LIBUSB_API_VERSION = 0x0100010A
# </ul>

LIBUSB_API_VERSION = 0x0100010A

# \def LIBUSBX_API_VERSION
# \ingroup libusb_misc
#
# This is the older spelling, kept for backwards compatibility of code
# needing to test for older library versions where the newer spelling
# did not exist.
LIBUSBX_API_VERSION = LIBUSB_API_VERSION

# \ingroup libusb::misc
# Convert a 16-bit value from host-endian to little-endian format. On
# little endian systems, this function does nothing. On big endian systems,
# the bytes are swapped.
# :param x: the host-endian value to convert
# :returns: the value in little-endian byte order

# static inline
@CFUNC(ct.c_uint16, ct.c_uint16)
def cpu_to_le16(x):

    class Tmp(ct.Union):
        _fields_ = [
        ("b8",  (ct.c_uint8 * 2)),
        ("b16", ct.c_uint16),
    ]

    tmp = Tmp()
    tmp.b8[1] = ct.c_uint8(x >> 8)
    tmp.b8[0] = ct.c_uint8(x & 0xff)

    return tmp.b16

# \def libusb.le16_to_cpu
# \ingroup libusb::misc
# Convert a 16-bit value from little-endian to host-endian format. On
# little endian systems, this function does nothing. On big endian systems,
# the bytes are swapped.
# :param x: the little-endian value to convert
# :returns: the value in host-endian byte order

le16_to_cpu = cpu_to_le16

### standard USB stuff ###

# \ingroup libusb::desc
# Device and/or Interface Class codes
class_code = ct.c_int
(
    # In the context of a \ref libusb.device_descriptor "device descriptor",
    # this bDeviceClass value indicates that each interface specifies its
    # own class information and all interfaces operate independently.
    LIBUSB_CLASS_PER_INTERFACE,

    # Audio class
    LIBUSB_CLASS_AUDIO,

    # Communications class
    LIBUSB_CLASS_COMM,

    # Human Interface Device class
    LIBUSB_CLASS_HID,

    # Physical
    LIBUSB_CLASS_PHYSICAL,

    # Image class
    LIBUSB_CLASS_IMAGE,
    LIBUSB_CLASS_PTP,  # legacy name from libusb-0.1 usb.h

    # Printer class
    LIBUSB_CLASS_PRINTER,

    # Mass storage class
    LIBUSB_CLASS_MASS_STORAGE,

    # Hub class
    LIBUSB_CLASS_HUB,

    # Data class
    LIBUSB_CLASS_DATA,

    # Smart Card
    LIBUSB_CLASS_SMART_CARD,

    # Content Security
    LIBUSB_CLASS_CONTENT_SECURITY,

    # Video
    LIBUSB_CLASS_VIDEO,

    # Personal Healthcare
    LIBUSB_CLASS_PERSONAL_HEALTHCARE,

    # Diagnostic Device
    LIBUSB_CLASS_DIAGNOSTIC_DEVICE,

    # Wireless class
    LIBUSB_CLASS_WIRELESS,

    # Miscellaneous class
    LIBUSB_CLASS_MISCELLANEOUS,

    # Application class
    LIBUSB_CLASS_APPLICATION,

    # Class is vendor-specific
    LIBUSB_CLASS_VENDOR_SPEC,

) = (0x00, 0x01, 0x02, 0x03, 0x05, 0x06, 0x06, 0x07, 0x08, 0x09,
     0x0a, 0x0b, 0x0d, 0x0e, 0x0f, 0xdc, 0xe0, 0xef, 0xfe, 0xff)

# \ingroup libusb::desc
# Descriptor types as defined by the USB specification.
descriptor_type = ct.c_int
(
    # Device descriptor. See libusb.device_descriptor.
    LIBUSB_DT_DEVICE,

    # Configuration descriptor. See libusb.config_descriptor.
    LIBUSB_DT_CONFIG,

    # String descriptor
    LIBUSB_DT_STRING,

    # Interface descriptor. See libusb.interface_descriptor.
    LIBUSB_DT_INTERFACE,

    # Endpoint descriptor. See libusb.endpoint_descriptor.
    LIBUSB_DT_ENDPOINT,

    # Interface Association Descriptor.
    # See libusb.interface_association_descriptor
    LIBUSB_DT_INTERFACE_ASSOCIATION,

    # BOS descriptor
    LIBUSB_DT_BOS,

    # Device Capability descriptor
    LIBUSB_DT_DEVICE_CAPABILITY,

    # HID descriptor
    LIBUSB_DT_HID,

    # HID report descriptor
    LIBUSB_DT_REPORT,

    # Physical descriptor
    LIBUSB_DT_PHYSICAL,

    # Hub descriptor
    LIBUSB_DT_HUB,

    # SuperSpeed Hub descriptor
    LIBUSB_DT_SUPERSPEED_HUB,

    # SuperSpeed Endpoint Companion descriptor
    LIBUSB_DT_SS_ENDPOINT_COMPANION,

) = (0x01, 0x02, 0x03, 0x04, 0x05, 0x0b, 0x0f,
     0x10, 0x21, 0x22, 0x23, 0x29, 0x2a, 0x30)

# Descriptor sizes per descriptor type
LIBUSB_DT_DEVICE_SIZE                = 18
LIBUSB_DT_CONFIG_SIZE                = 9
LIBUSB_DT_INTERFACE_SIZE             = 9
LIBUSB_DT_ENDPOINT_SIZE              = 7
LIBUSB_DT_ENDPOINT_AUDIO_SIZE        = 9  # Audio extension
LIBUSB_DT_HUB_NONVAR_SIZE            = 7
LIBUSB_DT_SS_ENDPOINT_COMPANION_SIZE = 6
LIBUSB_DT_BOS_SIZE                   = 5
LIBUSB_DT_DEVICE_CAPABILITY_SIZE     = 3

# BOS descriptor sizes
LIBUSB_BT_USB_2_0_EXTENSION_SIZE        = 7
LIBUSB_BT_SS_USB_DEVICE_CAPABILITY_SIZE = 10
LIBUSB_BT_CONTAINER_ID_SIZE             = 20
LIBUSB_BT_PLATFORM_DESCRIPTOR_MIN_SIZE  = 20

# We unwrap the BOS => define its max size
LIBUSB_DT_BOS_MAX_SIZE = (LIBUSB_DT_BOS_SIZE
                          + LIBUSB_BT_USB_2_0_EXTENSION_SIZE
                          + LIBUSB_BT_SS_USB_DEVICE_CAPABILITY_SIZE
                          + LIBUSB_BT_CONTAINER_ID_SIZE)

LIBUSB_ENDPOINT_ADDRESS_MASK = 0x0f  # in bEndpointAddress
LIBUSB_ENDPOINT_DIR_MASK     = 0x80

# \ingroup libusb::desc
# Endpoint direction. Values for bit 7 of the
# \ref libusb.endpoint_descriptor::bEndpointAddress "endpoint address" scheme.

endpoint_direction = ct.c_int
(
    # Out: host-to-device
    LIBUSB_ENDPOINT_OUT,

    # In: device-to-host
    LIBUSB_ENDPOINT_IN,

) = (0x00, 0x80)

LIBUSB_TRANSFER_TYPE_MASK = 0x03  # in bmAttributes

# \ingroup libusb::desc
# Endpoint transfer type. Values for bits 0:1 of the
# \ref libusb.endpoint_descriptor::bmAttributes "endpoint attributes" field.

endpoint_transfer_type = ct.c_int
(
    # Control endpoint
    LIBUSB_ENDPOINT_TRANSFER_TYPE_CONTROL,

    # Isochronous endpoint
    LIBUSB_ENDPOINT_TRANSFER_TYPE_ISOCHRONOUS,

    # Bulk endpoint
    LIBUSB_ENDPOINT_TRANSFER_TYPE_BULK,

    # Interrupt endpoint
    LIBUSB_ENDPOINT_TRANSFER_TYPE_INTERRUPT,

) = (0x0, 0x1, 0x2, 0x3)

# \ingroup libusb::misc
# Standard requests, as defined in table 9-5 of the USB 3.0 specifications
standard_request = ct.c_int
(
    # Request status of the specific recipient
    LIBUSB_REQUEST_GET_STATUS,

    # Clear or disable a specific feature
    LIBUSB_REQUEST_CLEAR_FEATURE,

    # 0x02 is reserved

    # Set or enable a specific feature
    LIBUSB_REQUEST_SET_FEATURE,

    # 0x04 is reserved

    # Set device address for all future accesses
    LIBUSB_REQUEST_SET_ADDRESS,

    # Get the specified descriptor
    LIBUSB_REQUEST_GET_DESCRIPTOR,

    # Used to update existing descriptors or add new descriptors
    LIBUSB_REQUEST_SET_DESCRIPTOR,

    # Get the current device configuration value
    LIBUSB_REQUEST_GET_CONFIGURATION,

    # Set device configuration
    LIBUSB_REQUEST_SET_CONFIGURATION,

    # Return the selected alternate setting for the specified interface
    LIBUSB_REQUEST_GET_INTERFACE,

    # Select an alternate interface for the specified interface
    LIBUSB_REQUEST_SET_INTERFACE,

    # Set then report an endpoint's synchronization frame
    LIBUSB_REQUEST_SYNCH_FRAME,

    # Sets both the U1 and U2 Exit Latency
    LIBUSB_REQUEST_SET_SEL,

    # Delay from the time a host transmits a packet to the time it is
    # received by the device.
    LIBUSB_SET_ISOCH_DELAY,

) = (0x00, 0x01, 0x03, 0x05, 0x06, 0x07, 0x08,
     0x09, 0x0a, 0x0b, 0x0c, 0x30, 0x31)

# \ingroup libusb::misc
# Request type bits of the
# \ref libusb.control_setup::bmRequestType "bmRequestType" field in control
# transfers.
request_type = ct.c_int
(
    # Standard
    LIBUSB_REQUEST_TYPE_STANDARD,

    # Class
    LIBUSB_REQUEST_TYPE_CLASS,

    # Vendor
    LIBUSB_REQUEST_TYPE_VENDOR,

    # Reserved
    LIBUSB_REQUEST_TYPE_RESERVED

) = (0x00 << 5, 0x01 << 5, 0x02 << 5, 0x03 << 5)

# \ingroup libusb::misc
# Recipient bits of the
# \ref libusb.control_setup::bmRequestType "bmRequestType" field in control
# transfers. Values 4 through 31 are reserved.
request_recipient = ct.c_int
(
    # Device
    LIBUSB_RECIPIENT_DEVICE,

    # Interface
    LIBUSB_RECIPIENT_INTERFACE,

    # Endpoint
    LIBUSB_RECIPIENT_ENDPOINT,

    # Other
    LIBUSB_RECIPIENT_OTHER,

) = (0x00, 0x01, 0x02, 0x03)

LIBUSB_ISO_SYNC_TYPE_MASK = 0x0c

# \ingroup libusb::desc
# Synchronization type for isochronous endpoints. Values for bits 2:3 of the
# \ref libusb.endpoint_descriptor::bmAttributes "bmAttributes" field in
# libusb.endpoint_descriptor.

iso_sync_type = ct.c_int
(
    # No synchronization
    LIBUSB_ISO_SYNC_TYPE_NONE,

    # Asynchronous
    LIBUSB_ISO_SYNC_TYPE_ASYNC,

    # Adaptive
    LIBUSB_ISO_SYNC_TYPE_ADAPTIVE,

    # Synchronous
    LIBUSB_ISO_SYNC_TYPE_SYNC

) = (0, 1, 2, 3)

LIBUSB_ISO_USAGE_TYPE_MASK = 0x30

# \ingroup libusb::desc
# Usage type for isochronous endpoints. Values for bits 4:5 of the
# \ref libusb.endpoint_descriptor::bmAttributes "bmAttributes" field in
# libusb.endpoint_descriptor.

iso_usage_type = ct.c_int
(
    # Data endpoint
    LIBUSB_ISO_USAGE_TYPE_DATA,

    # Feedback endpoint
    LIBUSB_ISO_USAGE_TYPE_FEEDBACK,

    # Implicit feedback Data endpoint
    LIBUSB_ISO_USAGE_TYPE_IMPLICIT,

) = (0x0, 0x1, 0x2)

# \ingroup libusb::desc
# Supported speeds (wSpeedSupported) bitfield. Indicates what
# speeds the device supports.

supported_speed = ct.c_int
(
    # Low speed operation supported (1.5MBit/s).
    LIBUSB_LOW_SPEED_OPERATION,

    # Full speed operation supported (12MBit/s).
    LIBUSB_FULL_SPEED_OPERATION,

    # High speed operation supported (480MBit/s).
    LIBUSB_HIGH_SPEED_OPERATION,

    # Superspeed operation supported (5000MBit/s).
    LIBUSB_SUPER_SPEED_OPERATION,

) = (1 << 0, 1 << 1, 1 << 2, 1 << 3)

# \ingroup libusb::desc
# Masks for the bits of the
# \ref libusb.usb_2_0_extension_descriptor::bmAttributes "bmAttributes" field
# of the USB 2.0 Extension descriptor.

usb_2_0_extension_attributes = ct.c_int
(
    # Supports Link Power Management (LPM)
    LIBUSB_BM_LPM_SUPPORT,

) = (1 << 1,)

# \ingroup libusb::desc
# Masks for the bits of the
# \ref libusb.ss_usb_device_capability_descriptor::bmAttributes "bmAttributes" field
# field of the SuperSpeed USB Device Capability descriptor.

ss_usb_device_capability_attributes = ct.c_int
(
    # Supports Latency Tolerance Messages (LTM)
    LIBUSB_BM_LTM_SUPPORT,

) = (1 << 1,)

# \ingroup libusb::desc
# USB capability types

bos_type = ct.c_int
(
    # Wireless USB device capability
    LIBUSB_BT_WIRELESS_USB_DEVICE_CAPABILITY,

    # USB 2.0 extensions
    LIBUSB_BT_USB_2_0_EXTENSION,

    # SuperSpeed USB device capability
    LIBUSB_BT_SS_USB_DEVICE_CAPABILITY,

    # Container ID type
    LIBUSB_BT_CONTAINER_ID,

    # Platform descriptor
    LIBUSB_BT_PLATFORM_DESCRIPTOR,

) = (0x01, 0x02, 0x03, 0x04, 0x05)

# \ingroup libusb::desc
# A structure representing the standard USB device descriptor. This
# descriptor is documented in section 9.6.1 of the USB 3.0 specification.
# All multiple-byte fields are represented in host-endian format.

class device_descriptor(ct.Structure):
    _fields_ = [

    # Size of this descriptor (in bytes)
    ("bLength", ct.c_uint8),

    # Descriptor type. Will have value
    # \ref libusb.descriptor_type::LIBUSB_DT_DEVICE LIBUSB_DT_DEVICE in this
    # context.
    ("bDescriptorType", ct.c_uint8),

    # USB specification release number in binary-coded decimal. A value of
    # 0x0200 indicates USB 2.0, 0x0110 indicates USB 1.1, etc.
    ("bcdUSB", ct.c_uint16),

    # USB-IF class code for the device. See \ref libusb.class_code.
    ("bDeviceClass", ct.c_uint8),

    # USB-IF subclass code for the device, qualified by the bDeviceClass
    # value
    ("bDeviceSubClass", ct.c_uint8),

    # USB-IF protocol code for the device, qualified by the bDeviceClass and
    # bDeviceSubClass values
    ("bDeviceProtocol", ct.c_uint8),

    # Maximum packet size for endpoint 0
    ("bMaxPacketSize0", ct.c_uint8),

    # USB-IF vendor ID
    ("idVendor", ct.c_uint16),

    # USB-IF product ID
    ("idProduct", ct.c_uint16),

    # Device release number in binary-coded decimal
    ("bcdDevice", ct.c_uint16),

    # Index of string descriptor describing manufacturer
    ("iManufacturer", ct.c_uint8),

    # Index of string descriptor describing product
    ("iProduct", ct.c_uint8),

    # Index of string descriptor containing device serial number
    ("iSerialNumber", ct.c_uint8),

    # Number of possible configurations
    ("bNumConfigurations", ct.c_uint8),
]

# \ingroup libusb::desc
# A structure representing the standard USB endpoint descriptor. This
# descriptor is documented in section 9.6.6 of the USB 3.0 specification.
# All multiple-byte fields are represented in host-endian format.

class endpoint_descriptor(ct.Structure):
    _fields_ = [

    # Size of this descriptor (in bytes)
    ("bLength", ct.c_uint8),

    # Descriptor type. Will have value
    # \ref libusb.descriptor_type::LIBUSB_DT_ENDPOINT LIBUSB_DT_ENDPOINT in
    # this context.
    ("bDescriptorType", ct.c_uint8),

    # The address of the endpoint described by this descriptor. Bits 0:3 are
    # the endpoint number. Bits 4:6 are reserved. Bit 7 indicates direction,
    # see \ref libusb.endpoint_direction.
    ("bEndpointAddress", ct.c_uint8),

    # Attributes which apply to the endpoint when it is configured using
    # the bConfigurationValue. Bits 0:1 determine the transfer type and
    # correspond to \ref libusb.endpoint_transfer_type. Bits 2:3 are only used
    # for isochronous endpoints and correspond to \ref libusb.iso_sync_type.
    # Bits 4:5 are also only used for isochronous endpoints and correspond to
    # \ref libusb.iso_usage_type. Bits 6:7 are reserved.
    ("bmAttributes", ct.c_uint8),

    # Maximum packet size this endpoint is capable of sending/receiving.
    ("wMaxPacketSize", ct.c_uint16),

    # Interval for polling endpoint for data transfers.
    ("bInterval", ct.c_uint8),

    # For audio devices only: the rate at which synchronization feedback
    # is provided.
    ("bRefresh", ct.c_uint8),

    # For audio devices only: the address if the synch endpoint
    ("bSynchAddress", ct.c_uint8),

    # Extra descriptors. If libusb encounters unknown endpoint descriptors,
    # it will store them here, should you wish to parse them.
    ("extra", ct.POINTER(ct.c_ubyte)),

    # Length of the extra descriptors, in bytes. Must be non-negative.
    ("extra_length", ct.c_int),
]

# \ingroup libusb_desc
# A structure representing the standard USB interface association descriptor.
# This descriptor is documented in section 9.6.4 of the USB 3.0 specification.
# All multiple-byte fields are represented in host-endian format.

class interface_association_descriptor(ct.Structure):
    _fields_ = [

    # Size of this descriptor (in bytes)
    ("bLength", ct.c_uint8),

    # Descriptor type. Will have value
    # \ref libusb.descriptor_type::LIBUSB_DT_INTERFACE_ASSOCIATION
    # LIBUSB_DT_INTERFACE_ASSOCIATION in this context.
    ("bDescriptorType", ct.c_uint8),

    # Interface number of the first interface that is associated
    # with this function
    ("bFirstInterface", ct.c_uint8),

    # Number of contiguous interfaces that are associated with
    # this function
    ("bInterfaceCount", ct.c_uint8),

    # USB-IF class code for this function.
    # A value of zero is not allowed in this descriptor.
    # If this field is 0xff, the function class is vendor-specific.
    # All other values are reserved for assignment by the USB-IF.
    ("bFunctionClass", ct.c_uint8),

    # USB-IF subclass code for this function.
    # If this field is not set to 0xff, all values are reserved
    # for assignment by the USB-IF
    ("bFunctionSubClass", ct.c_uint8),

    # USB-IF protocol code for this function.
    # These codes are qualified by the values of the bFunctionClass
    # and bFunctionSubClass fields.
    ("bFunctionProtocol", ct.c_uint8),

    # Index of string descriptor describing this function
    ("iFunction", ct.c_uint8),
]

# \ingroup libusb_desc
# Structure containing an array of 0 or more interface association
# descriptors

class interface_association_descriptor_array(ct.Structure):
    _fields_ = [

    # Array of interface association descriptors. The size of this array
    # is determined by the length field.
    ("iad", ct.POINTER(interface_association_descriptor)),

    # Number of interface association descriptors contained. Read-only.
    ("length", ct.c_int),
]

# \ingroup libusb::desc
# A structure representing the standard USB interface descriptor. This
# descriptor is documented in section 9.6.5 of the USB 3.0 specification.
# All multiple-byte fields are represented in host-endian format.

class interface_descriptor(ct.Structure):
    _fields_ = [

    # Size of this descriptor (in bytes)
    ("bLength", ct.c_uint8),

    # Descriptor type. Will have value
    # \ref libusb.descriptor_type::LIBUSB_DT_INTERFACE LIBUSB_DT_INTERFACE
    # in this context.
    ("bDescriptorType", ct.c_uint8),

    # Number of this interface
    ("bInterfaceNumber", ct.c_uint8),

    # Value used to select this alternate setting for this interface
    ("bAlternateSetting", ct.c_uint8),

    # Number of endpoints used by this interface (excluding the control
    # endpoint).
    ("bNumEndpoints", ct.c_uint8),

    # USB-IF class code for this interface. See \ref libusb.class_code.
    ("bInterfaceClass", ct.c_uint8),

    # USB-IF subclass code for this interface, qualified by the
    # bInterfaceClass value
    ("bInterfaceSubClass", ct.c_uint8),

    # USB-IF protocol code for this interface, qualified by the
    # bInterfaceClass and bInterfaceSubClass values
    ("bInterfaceProtocol", ct.c_uint8),

    # Index of string descriptor describing this interface
    ("iInterface", ct.c_uint8),

    # Array of endpoint descriptors. This length of this array is determined
    # by the bNumEndpoints field.
    ("endpoint", ct.POINTER(endpoint_descriptor)),

    # Extra descriptors. If libusb encounters unknown interface descriptors,
    # it will store them here, should you wish to parse them.
    ("extra", ct.POINTER(ct.c_ubyte)),

    # Length of the extra descriptors, in bytes. Must be non-negative.
    ("extra_length", ct.c_int),
]

# \ingroup libusb::desc
# A collection of alternate settings for a particular USB interface.

class interface(ct.Structure):
    _fields_ = [

    # Array of interface descriptors. The length of this array is determined
    # by the num_altsetting field.
    ("altsetting", ct.POINTER(interface_descriptor)),

    # The number of alternate settings that belong to this interface.
    # Must be non-negative.
    ("num_altsetting", ct.c_int),
]

# \ingroup libusb::desc
# A structure representing the standard USB configuration descriptor. This
# descriptor is documented in section 9.6.3 of the USB 3.0 specification.
# All multiple-byte fields are represented in host-endian format.

class config_descriptor(ct.Structure):
    _fields_ = [

    # Size of this descriptor (in bytes)
    ("bLength", ct.c_uint8),

    # Descriptor type. Will have value
    # \ref libusb.descriptor_type::LIBUSB_DT_CONFIG LIBUSB_DT_CONFIG
    # in this context.
    ("bDescriptorType", ct.c_uint8),

    # Total length of data returned for this configuration
    ("wTotalLength", ct.c_uint16),

    # Number of interfaces supported by this configuration
    ("bNumInterfaces", ct.c_uint8),

    # Identifier value for this configuration
    ("bConfigurationValue", ct.c_uint8),

    # Index of string descriptor describing this configuration
    ("iConfiguration", ct.c_uint8),

    # Configuration characteristics
    ("bmAttributes", ct.c_uint8),

    # Maximum power consumption of the USB device from this bus in this
    # configuration when the device is fully operation. Expressed in units
    # of 2 mA when the device is operating in high-speed mode and in units
    # of 8 mA when the device is operating in super-speed mode.
    ("MaxPower", ct.c_uint8),

    # Array of interfaces supported by this configuration. The length of
    # this array is determined by the bNumInterfaces field.
    ("interface", ct.POINTER(interface)),

    # Extra descriptors. If libusb encounters unknown configuration
    # descriptors, it will store them here, should you wish to parse them.
    ("extra", ct.POINTER(ct.c_ubyte)),

    # Length of the extra descriptors, in bytes. Must be non-negative.
    ("extra_length", ct.c_int),
]

# \ingroup libusb::desc
# A structure representing the superspeed endpoint companion
# descriptor. This descriptor is documented in section 9.6.7 of
# the USB 3.0 specification. All multiple-byte fields are represented in
# host-endian format.

class ss_endpoint_companion_descriptor(ct.Structure):
    _fields_ = [

    # Size of this descriptor (in bytes)
    ("bLength", ct.c_uint8),

    # Descriptor type. Will have value
    # \ref libusb.descriptor_type::LIBUSB_DT_SS_ENDPOINT_COMPANION in
    # this context.
    ("bDescriptorType", ct.c_uint8),

    # The maximum number of packets the endpoint can send or
    #  receive as part of a burst.
    ("bMaxBurst", ct.c_uint8),

    # In bulk EP: bits 4:0 represents the maximum number of
    # streams the EP supports. In isochronous EP: bits 1:0
    # represents the Mult - a zero based value that determines
    # the maximum number of packets within a service interval
    ("bmAttributes", ct.c_uint8),

    # The total number of bytes this EP will transfer every
    # service interval. Valid only for periodic EPs.
    ("wBytesPerInterval", ct.c_uint16),
]

# \ingroup libusb::desc
# A generic representation of a BOS Device Capability descriptor. It is
# advised to check bDevCapabilityType and call the matching
# libusb.get_*_descriptor function to get a structure fully matching the type.

class bos_dev_capability_descriptor(ct.Structure):
    _fields_ = [

    # Size of this descriptor (in bytes)
    ("bLength", ct.c_uint8),

    # Descriptor type. Will have value
    # \ref libusb.descriptor_type::LIBUSB_DT_DEVICE_CAPABILITY
    # LIBUSB_DT_DEVICE_CAPABILITY in this context.
    ("bDescriptorType", ct.c_uint8),

    # Device Capability type
    ("bDevCapabilityType", ct.c_uint8),

    # Device Capability data (bLength - 3 bytes)
    ("dev_capability_data", (ct.c_uint8 * 0)),
]

# \ingroup libusb::desc
# A structure representing the Binary Device Object Store (BOS) descriptor.
# This descriptor is documented in section 9.6.2 of the USB 3.0 specification.
# All multiple-byte fields are represented in host-endian format.

class bos_descriptor(ct.Structure):
    _fields_ = [

    # Size of this descriptor (in bytes)
    ("bLength", ct.c_uint8),

    # Descriptor type. Will have value
    # \ref libusb.descriptor_type::LIBUSB_DT_BOS LIBUSB_DT_BOS
    # in this context.
    ("bDescriptorType", ct.c_uint8),

    # Length of this descriptor and all of its sub descriptors
    ("wTotalLength", ct.c_uint16),

    # The number of separate device capability descriptors in
    # the BOS
    ("bNumDeviceCaps", ct.c_uint8),

    # bNumDeviceCap Device Capability Descriptors
    ("dev_capability", (ct.POINTER(bos_dev_capability_descriptor) * 0)),
]

# \ingroup libusb::desc
# A structure representing the USB 2.0 Extension descriptor
# This descriptor is documented in section 9.6.2.1 of the USB 3.0 specification.
# All multiple-byte fields are represented in host-endian format.

class usb_2_0_extension_descriptor(ct.Structure):
    _fields_ = [

    # Size of this descriptor (in bytes)
    ("bLength", ct.c_uint8),

    # Descriptor type. Will have value
    # \ref libusb.descriptor_type::LIBUSB_DT_DEVICE_CAPABILITY
    # LIBUSB_DT_DEVICE_CAPABILITY in this context.
    ("bDescriptorType", ct.c_uint8),

    # Capability type. Will have value
    # \ref libusb.bos_type::LIBUSB_BT_USB_2_0_EXTENSION
    # LIBUSB_BT_USB_2_0_EXTENSION in this context.
    ("bDevCapabilityType", ct.c_uint8),

    # Bitmap encoding of supported device level features.
    # A value of one in a bit location indicates a feature is
    # supported; a value of zero indicates it is not supported.
    # See \ref libusb.usb_2_0_extension_attributes.
    ("bmAttributes", ct.c_uint32),
]

# \ingroup libusb::desc
# A structure representing the SuperSpeed USB Device Capability descriptor
# This descriptor is documented in section 9.6.2.2 of the USB 3.0 specification.
# All multiple-byte fields are represented in host-endian format.

class ss_usb_device_capability_descriptor(ct.Structure):
    _fields_ = [

    # Size of this descriptor (in bytes)
    ("bLength", ct.c_uint8),

    # Descriptor type. Will have value
    # \ref libusb.descriptor_type::LIBUSB_DT_DEVICE_CAPABILITY
    # LIBUSB_DT_DEVICE_CAPABILITY in this context.
    ("bDescriptorType", ct.c_uint8),

    # Capability type. Will have value
    # \ref libusb.bos_type::LIBUSB_BT_SS_USB_DEVICE_CAPABILITY
    # LIBUSB_BT_SS_USB_DEVICE_CAPABILITY in this context.
    ("bDevCapabilityType", ct.c_uint8),

    # Bitmap encoding of supported device level features.
    # A value of one in a bit location indicates a feature is
    # supported; a value of zero indicates it is not supported.
    # See \ref libusb.ss_usb_device_capability_attributes.
    ("bmAttributes", ct.c_uint8),

    # Bitmap encoding of the speed supported by this device when
    # operating in SuperSpeed mode. See \ref libusb.supported_speed.
    ("wSpeedSupported", ct.c_uint16),

    # The lowest speed at which all the functionality supported
    # by the device is available to the user. For example if the
    # device supports all its functionality when connected at
    # full speed and above then it sets this value to 1.
    ("bFunctionalitySupport", ct.c_uint8),

    # U1 Device Exit Latency.
    ("bU1DevExitLat", ct.c_uint8),

    # U2 Device Exit Latency.
    ("bU2DevExitLat", ct.c_uint16),
]

# \ingroup libusb::desc
# A structure representing the Container ID descriptor.
# This descriptor is documented in section 9.6.2.3 of the USB 3.0 specification.
# All multiple-byte fields, except UUIDs, are represented in host-endian format.

class container_id_descriptor(ct.Structure):
    _fields_ = [

    # Size of this descriptor (in bytes)
    ("bLength", ct.c_uint8),

    # Descriptor type. Will have value
    # \ref libusb.descriptor_type::LIBUSB_DT_DEVICE_CAPABILITY
    # LIBUSB_DT_DEVICE_CAPABILITY in this context.
    ("bDescriptorType", ct.c_uint8),

    # Capability type. Will have value
    # \ref libusb.bos_type::LIBUSB_BT_CONTAINER_ID
    # LIBUSB_BT_CONTAINER_ID in this context.
    ("bDevCapabilityType", ct.c_uint8),

    # Reserved field
    ("bReserved", ct.c_uint8),

    # 128 bit UUID
    ("ContainerID", (ct.c_uint8 * 16)),
]

# \ingroup libusb_desc
# A structure representing a Platform descriptor.
# This descriptor is documented in section 9.6.2.4 of the USB 3.2 specification.

class platform_descriptor(ct.Structure):
    _fields_ = [

    # Size of this descriptor (in bytes)
    ("bLength", ct.c_uint8),

    # Descriptor type. Will have value
    # \ref libusb.descriptor_type::LIBUSB_DT_DEVICE_CAPABILITY
    # LIBUSB_DT_DEVICE_CAPABILITY in this context.
    ("bDescriptorType", ct.c_uint8),

    # Capability type. Will have value
    # \ref libusb.capability_type::LIBUSB_BT_PLATFORM_DESCRIPTOR
    # LIBUSB_BT_CONTAINER_ID in this context.
    ("bDevCapabilityType", ct.c_uint8),

    # Reserved field
    ("bReserved", ct.c_uint8),

    # 128 bit UUID
    ("PlatformCapabilityUUID", (ct.c_uint8 * 16)),

    # Capability data (bLength - 20)
    ("CapabilityData", (ct.c_uint8 * 0)),
]

# \ingroup libusb::asyncio
# Setup packet for control transfers.
# if defined(_MSC_VER) || defined(__WATCOMC__)
# pragma pack(push, 1)
# endif
class control_setup(ct.Structure):
    _fields_ = [

    # Request type. Bits 0:4 determine recipient, see
    # \ref libusb.request_recipient. Bits 5:6 determine type, see
    # \ref libusb.request_type. Bit 7 determines data transfer direction, see
    # \ref libusb.endpoint_direction.
    ("bmRequestType", ct.c_uint8),

    # Request. If the type bits of bmRequestType are equal to
    # \ref libusb.request_type::LIBUSB_REQUEST_TYPE_STANDARD
    # "LIBUSB_REQUEST_TYPE_STANDARD" then this field refers to
    # \ref libusb.standard_request. For other cases, use of this field is
    # application-specific.
    ("bRequest", ct.c_uint8),

    # Value. Varies according to request
    ("wValue", ct.c_uint16),

    # Index. Varies according to request, typically used to pass an index
    # or offset
    ("wIndex", ct.c_uint16),

    # Number of bytes to transfer
    ("wLength", ct.c_uint16),
]
# if defined(_MSC_VER) || defined(__WATCOMC__)
# pragma pack(pop)
# endif

LIBUSB_CONTROL_SETUP_SIZE = ct.sizeof(control_setup)

### libusb ###

# \ingroup libusb::lib
# Structure providing the version of the libusb runtime

class version(ct.Structure):
    _fields_ = [

    # Library major version.
    ("major", ct.c_uint16),

    # Library minor version.
    ("minor", ct.c_uint16),

    # Library micro version.
    ("micro", ct.c_uint16),

    # Library nano version.
    ("nano", ct.c_uint16),

    # Library release candidate suffix string, e.g. "-rc4".
    ("rc", ct.c_char_p),

    # For ABI compatibility only.
    ("describe", ct.c_char_p),
]

# \ingroup libusb::lib
# Structure representing a libusb session. The concept of individual libusb
# sessions allows for your program to use two libraries (or dynamically
# load two modules) which both independently use libusb. This will prevent
# interference between the individual libusb users - for example
# libusb.set_option() will not affect the other user of the library, and
# libusb.exit() will not destroy resources that the other user is still
# using.
#
# Sessions are created by libusb.init_context() and destroyed through libusb.exit().
# If your application is guaranteed to only ever include a single libusb
# user (i.e. you), you do not have to worry about contexts: pass NULL in
# every function call where a context is required, and the default context
# will be used. Note that libusb.set_option(NULL, ...) is special, and adds
# an option to a list of default options for new contexts.
#
# For more information, see \ref libusb.contexts.

class context(ct.Structure): pass

# \ingroup libusb::dev
# Structure representing a USB device detected on the system. This is an
# opaque type for which you are only ever provided with a pointer, usually
# originating from libusb.get_device_list() or libusb.hotplug_register_callback().
#
# Certain operations can be performed on a device, but in order to do any
# I/O you will have to first obtain a device handle using libusb.open().
#
# Devices are reference counted with libusb.ref_device() and
# libusb.unref_device(), and are freed when the reference count reaches 0.
# New devices presented by libusb.get_device_list() have a reference count of
# 1, and libusb.free_device_list() can optionally decrease the reference count
# on all devices in the list. libusb.open() adds another reference which is
# later destroyed by libusb.close().

class device(ct.Structure): pass

# \ingroup libusb::dev
# Structure representing a handle on a USB device. This is an opaque type for
# which you are only ever provided with a pointer, usually originating from
# libusb.open().
#
# A device handle is used to perform I/O and other operations. When finished
# with a device handle, you should call libusb.close().

class device_handle(ct.Structure): pass

# \ingroup libusb::dev
# Speed codes. Indicates the speed at which the device is operating.

speed = ct.c_int
(
    # The OS doesn't report or know the device speed.
    LIBUSB_SPEED_UNKNOWN,

    # The device is operating at low speed (1.5MBit/s).
    LIBUSB_SPEED_LOW,

    # The device is operating at full speed (12MBit/s).
    LIBUSB_SPEED_FULL,

    # The device is operating at high speed (480MBit/s).
    LIBUSB_SPEED_HIGH,

    # The device is operating at super speed (5000MBit/s).
    LIBUSB_SPEED_SUPER,

    # The device is operating at super speed plus (10000MBit/s).
    LIBUSB_SPEED_SUPER_PLUS,

) = (0, 1, 2, 3, 4, 5)

# \ingroup libusb::misc
# Error codes. Most libusb functions return 0 on success or one of these
# codes on failure.
# You can call libusb.error_name() to retrieve a string representation of an
# error code or libusb.strerror() to get an end-user suitable description of
# an error code.

error = ct.c_int
(
    # Success (no error)
    LIBUSB_SUCCESS,

    # Input/output error
    LIBUSB_ERROR_IO,

    # Invalid parameter
    LIBUSB_ERROR_INVALID_PARAM,

    # Access denied (insufficient permissions)
    LIBUSB_ERROR_ACCESS,

    # No such device (it may have been disconnected)
    LIBUSB_ERROR_NO_DEVICE,

    # Entity not found
    LIBUSB_ERROR_NOT_FOUND,

    # Resource busy
    LIBUSB_ERROR_BUSY,

    # Operation timed out
    LIBUSB_ERROR_TIMEOUT,

    # Overflow
    LIBUSB_ERROR_OVERFLOW,

    # Pipe error
    LIBUSB_ERROR_PIPE,

    # System call interrupted (perhaps due to signal)
    LIBUSB_ERROR_INTERRUPTED,

    # Insufficient memory
    LIBUSB_ERROR_NO_MEM,

    # Operation not supported or unimplemented on this platform
    LIBUSB_ERROR_NOT_SUPPORTED,

    # NB: Remember to update LIBUSB_ERROR_COUNT below as well as the
    # message strings in strerror.c when adding new error codes here.

    # Other error
    LIBUSB_ERROR_OTHER,

) = (0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12, -99)

# Total number of error codes in enum libusb.error
LIBUSB_ERROR_COUNT = 14

# \ingroup libusb::asyncio
# Transfer type

transfer_type = ct.c_int
(
    # Control transfer
    LIBUSB_TRANSFER_TYPE_CONTROL,

    # Isochronous transfer
    LIBUSB_TRANSFER_TYPE_ISOCHRONOUS,

    # Bulk transfer
    LIBUSB_TRANSFER_TYPE_BULK,

    # Interrupt transfer
    LIBUSB_TRANSFER_TYPE_INTERRUPT,

    # Bulk stream transfer
    LIBUSB_TRANSFER_TYPE_BULK_STREAM,

) = (0, 1, 2, 3, 4)

# \ingroup libusb::asyncio
# Transfer status codes
transfer_status = ct.c_int
(
    # Transfer completed without error. Note that this does not indicate
    # that the entire amount of requested data was transferred.
    LIBUSB_TRANSFER_COMPLETED,

    # Transfer failed
    LIBUSB_TRANSFER_ERROR,

    # Transfer timed out
    LIBUSB_TRANSFER_TIMED_OUT,

    # Transfer was cancelled
    LIBUSB_TRANSFER_CANCELLED,

    # For bulk/interrupt endpoints: halt condition detected (endpoint
    # stalled). For control endpoints: control request not supported.
    LIBUSB_TRANSFER_STALL,

    # Device was disconnected
    LIBUSB_TRANSFER_NO_DEVICE,

    # Device sent more data than requested
    LIBUSB_TRANSFER_OVERFLOW,

    # NB! Remember to update libusb.error_name()
    # when adding new status codes here.

) = range(0, 7)

# \ingroup libusb::asyncio
# libusb.transfer_flags values

transfer_flags = ct.c_int
(
    # Report short frames as errors
    LIBUSB_TRANSFER_SHORT_NOT_OK,

    # Automatically free() transfer buffer during libusb.free_transfer().
    # Note that buffers allocated with libusb.dev_mem_alloc() should not
    # be attempted freed in this way, since free() is not an appropriate
    # way to release such memory.
    LIBUSB_TRANSFER_FREE_BUFFER,

    # Automatically call libusb.free_transfer() after callback returns.
    # If this flag is set, it is illegal to call libusb.free_transfer()
    # from your transfer callback, as this will result in a double-free
    # when this flag is acted upon.
    LIBUSB_TRANSFER_FREE_TRANSFER,

    # Terminate transfers that are a multiple of the endpoint's
    # wMaxPacketSize with an extra zero length packet. This is useful
    # when a device protocol mandates that each logical request is
    # terminated by an incomplete packet (i.e. the logical requests are
    # not separated by other means).
    #
    # This flag only affects host-to-device transfers to bulk and interrupt
    # endpoints. In other situations, it is ignored.
    #
    # This flag only affects transfers with a length that is a multiple of
    # the endpoint's wMaxPacketSize. On transfers of other lengths, this
    # flag has no effect. Therefore, if you are working with a device that
    # needs a ZLP whenever the end of the logical request falls on a packet
    # boundary, then it is sensible to set this flag on <em>every</em>
    # transfer (you do not have to worry about only setting it on transfers
    # that end on the boundary).
    #
    # This flag is currently only supported on Linux.
    # On other systems, libusb.submit_transfer() will return
    # \ref LIBUSB_ERROR_NOT_SUPPORTED for every transfer where this
    # flag is set.
    #
    # Available since libusb-1.0.9.
    LIBUSB_TRANSFER_ADD_ZERO_PACKET,

) = (1 << 0, 1 << 1, 1 << 2, 1 << 3)

# \ingroup libusb::asyncio
# Isochronous packet descriptor.

class iso_packet_descriptor(ct.Structure):
    _fields_ = [

    # Length of data to request in this packet
    ("length", ct.c_uint),

    # Amount of data that was actually transferred
    ("actual_length", ct.c_uint),

    # Status code for this packet
    ("status", transfer_status),
]

class transfer(ct.Structure): pass

# \ingroup libusb::asyncio
# Asynchronous transfer callback function type. When submitting asynchronous
# transfers, you pass a pointer to a callback function of this type via the
# \ref libusb.transfer::callback "callback" member of the libusb.transfer
# structure. libusb will call this function later, when the transfer has
# completed or failed. See \ref libusb::asyncio for more information.
# :param transfer: The libusb.transfer struct the callback function is being
# notified about.

transfer_cb_fn = CFUNC(None, ct.POINTER(transfer))

# \ingroup libusb::asyncio
# The generic USB transfer structure. The user populates this structure and
# then submits it in order to request a transfer. After the transfer has
# completed, the library populates the transfer with the results and passes
# it back to the user.

transfer._fields_ = [

    # Handle of the device that this transfer will be submitted to
    ("dev_handle", ct.POINTER(device_handle)),

    # A bitwise OR combination of \ref libusb.transfer_flags.
    ("flags", ct.c_uint8),

    # Address of the endpoint where this transfer will be sent.
    ("endpoint", ct.c_ubyte),

    # Type of the transfer from \ref libusb.transfer_type
    ("type", ct.c_ubyte),

    # Timeout for this transfer in milliseconds. A value of 0 indicates no
    # timeout.
    ("timeout", ct.c_uint),

    # The status of the transfer. Read-only, and only for use within
    # transfer callback function.
    #
    # If this is an isochronous transfer, this field may read COMPLETED even
    # if there were errors in the frames. Use the
    # \ref libusb.iso_packet_descriptor::status "status" field in each packet
    # to determine if errors occurred.
    ("status", transfer_status),

    # Length of the data buffer. Must be non-negative.
    ("length", ct.c_int),

    # Actual length of data that was transferred. Read-only, and only for
    # use within transfer callback function. Not valid for isochronous
    # endpoint transfers.
    ("actual_length", ct.c_int),

    # Callback function. This will be invoked when the transfer completes,
    # fails, or is cancelled.
    ("callback", transfer_cb_fn),

    # User context data. Useful for associating specific data to a transfer
    # that can be accessed from within the callback function.
    #
    # This field may be set manually or is taken as the `user_data` parameter
    # of the following functions:
    # - libusb.fill_bulk_transfer()
    # - libusb.fill_bulk_stream_transfer()
    # - libusb.fill_control_transfer()
    # - libusb.fill_interrupt_transfer()
    # - libusb.fill_iso_transfer()
    ("user_data", ct.c_void_p),

    # Data buffer
    ("buffer", ct.POINTER(ct.c_ubyte)),

    # Number of isochronous packets. Only used for I/O with isochronous
    # endpoints. Must be non-negative.
    ("num_iso_packets", ct.c_int),

    # Isochronous packet descriptors, for isochronous transfers only.
    ("iso_packet_desc", (iso_packet_descriptor * 0)),
]

# \ingroup libusb::misc
# Capabilities supported by an instance of libusb on the current running
# platform. Test if the loaded library supports a given capability by calling
# \ref libusb.has_capability().

capability = ct.c_int
(
    # The libusb.has_capability() API is available.
    LIBUSB_CAP_HAS_CAPABILITY,

    # Hotplug support is available on this platform.
    LIBUSB_CAP_HAS_HOTPLUG,

    # The library can access HID devices without requiring user intervention.
    # Note that before being able to actually access an HID device, you may
    # still have to call additional libusb functions such as
    # \ref libusb.detach_kernel_driver().
    LIBUSB_CAP_HAS_HID_ACCESS,

    # The library supports detaching of the default USB driver, using
    # \ref libusb.detach_kernel_driver(), if one is set by the OS kernel
    LIBUSB_CAP_SUPPORTS_DETACH_KERNEL_DRIVER,

) = (0x0000, 0x0001, 0x0100, 0x0101)

# \ingroup libusb::lib
# Log message levels.

log_level = ct.c_int
(
    # (0) : No messages ever emitted by the library (default)
    LIBUSB_LOG_LEVEL_NONE,

    # (1) : Error messages are emitted
    LIBUSB_LOG_LEVEL_ERROR,

    # (2) : Warning and error messages are emitted
    LIBUSB_LOG_LEVEL_WARNING,

    # (3) : Informational, warning and error messages are emitted
    LIBUSB_LOG_LEVEL_INFO,

    # (4) : All messages are emitted
    LIBUSB_LOG_LEVEL_DEBUG,

) = (0, 1, 2, 3, 4)

# \ingroup libusb::lib
# Log callback mode.
#
# Since version 1.0.23, \ref LIBUSB_API_VERSION >= 0x01000107
#
# \see libusb.set_log_cb()

log_cb_mode = ct.c_int
(
    # Callback function handling all log messages.
    LIBUSB_LOG_CB_GLOBAL,

    # Callback function handling context related log messages.
    LIBUSB_LOG_CB_CONTEXT,

) = (1 << 0, 1 << 1)

# \ingroup libusb::lib
# Available option values for libusb.set_option() and libusb.init_context().

option = ct.c_int
(
    # Set the log message verbosity.
    #
    # This option must be provided an argument of type \ref libusb.log_level.
    # The default level is LIBUSB_LOG_LEVEL_NONE, which means no messages are ever
    # printed. If you choose to increase the message verbosity level, ensure
    # that your application does not close the stderr file descriptor.
    #
    # You are advised to use level LIBUSB_LOG_LEVEL_WARNING. libusb is conservative
    # with its message logging and most of the time, will only log messages that
    # explain error conditions and other oddities. This will help you debug
    # your software.
    #
    # If the LIBUSB_DEBUG environment variable was set when libusb was
    # initialized, this option does nothing: the message verbosity is fixed
    # to the value in the environment variable.
    #
    # If libusb was compiled without any message logging, this option does
    # nothing: you'll never get any messages.
    #
    # If libusb was compiled with verbose debug message logging, this option
    # does nothing: you'll always get messages from all levels.
    #
    LIBUSB_OPTION_LOG_LEVEL,

    # Use the UsbDk backend for a specific context, if available.
    #
    # This option should be set at initialization with libusb.init_context()
    # otherwise unspecified behavior may occur.
    #
    # Only valid on Windows. Ignored on all other platforms.
    #
    LIBUSB_OPTION_USE_USBDK,

    # Do not scan for devices
    #
    # With this option set, libusb will skip scanning devices in
    # libusb.init_context().
    #
    # Hotplug functionality will also be deactivated.
    #
    # The option is useful in combination with libusb.wrap_sys_device(),
    # which can access a device directly without prior device scanning.
    #
    # This is typically needed on Android, where access to USB devices
    # is limited.
    #
    # This option should only be used with libusb.init_context()
    # otherwise unspecified behavior may occur.
    #
    # Only valid on Linux. Ignored on all other platforms.
    #
    LIBUSB_OPTION_NO_DEVICE_DISCOVERY,

    # Set the context log callback function.
    #
    # Set the log callback function either on a context or globally. This
    # option must be provided an argument of type \ref libusb.log_cb.
    # Using this option with a NULL context is equivalent to calling
    # libusb.set_log_cb() with mode \ref LIBUSB_LOG_CB_GLOBAL.
    # Using it with a non-NULL context is equivalent to calling
    # libusb.set_log_cb() with mode \ref LIBUSB_LOG_CB_CONTEXT.
    #
    LIBUSB_OPTION_LOG_CB,

    LIBUSB_OPTION_MAX,

) = (0, 1, 2, 3, 4)
LIBUSB_OPTION_WEAK_AUTHORITY = LIBUSB_OPTION_NO_DEVICE_DISCOVERY

# \ingroup libusb::lib
# Callback function for handling log messages.
# \param ctx the context which is related to the log message, or NULL if it
#            is a global log message
# \param level the log level, see \ref libusb.log_level for a description
# \param str the log message
#
# Since version 1.0.23, \ref LIBUSB_API_VERSION >= 0x01000107
#
# \see libusb.set_log_cb()

log_cb = CFUNC(None, ct.POINTER(context), log_level, ct.c_char_p)

# \ingroup libusb_lib
# Structure used for setting options through \ref libusb.init_context.

class init_option(ct.Structure):
    class _Value(ct.Union):
        _fields_ = [
        ("ival",      ct.c_int),
        ("log_cbval", log_cb),]
    _fields_ = [
    # Which option to set
    ("option", option),
    # An integer value used by the option (if applicable).
    ("value", _Value),
]


get_version = CFUNC(ct.POINTER(version))(
    ("libusb_get_version", dll),)

init = CFUNC(ct.c_int,
    ct.POINTER(ct.POINTER(context)))(
    ("libusb_init", dll), (
    (1, "ctx"),))

try:
    init_context = CFUNC(ct.c_int,
        ct.POINTER(ct.POINTER(context)),
        ct.POINTER(init_option),
        ct.c_int)(
        ("libusb_init_context", dll), (
        (1, "ctx"),
        (1, "options"),
        (1, "num_options"),))
except: pass  # noqa: E722

exit = CFUNC(None,  # noqa: A001
    ct.POINTER(context))(
    ("libusb_exit", dll), (
    (1, "ctx"),))

set_debug = CFUNC(None,
    ct.POINTER(context),
    ct.c_int)(
    ("libusb_set_debug", dll), (
    (1, "ctx"),
    (1, "level"),))
# may be deprecated in the future in favor of lubusb.init_context()+libusb.set_option()

try:
    set_log_cb = CFUNC(None,
        ct.POINTER(context),
        log_cb,
        ct.c_int)(
        ("libusb_set_log_cb", dll), (
        (1, "ctx"),
        (1, "cb"),
        (1, "mode"),))
except: pass  # noqa: E722

has_capability = CFUNC(ct.c_int,
    ct.c_uint32)(
    ("libusb_has_capability", dll), (
    (1, "capability"),))

error_name = CFUNC(ct.c_char_p,
    ct.c_int)(
    ("libusb_error_name", dll), (
    (1, "errcode"),))

strerror = CFUNC(ct.c_char_p,
    ct.c_int)(
    ("libusb_strerror", dll), (
    (1, "errcode"),))

setlocale = CFUNC(ct.c_int,
    ct.c_char_p)(
    ("libusb_setlocale", dll), (
    (1, "locale"),))

get_device_list = CFUNC(ct.c_ssize_t,
    ct.POINTER(context),
    ct.POINTER(ct.POINTER(ct.POINTER(device))))(
    ("libusb_get_device_list", dll), (
    (1, "ctx"),
    (1, "list"),))

free_device_list = CFUNC(None,
    ct.POINTER(ct.POINTER(device)),
    ct.c_int)(
    ("libusb_free_device_list", dll), (
    (1, "list"),
    (1, "unref_devices"),))

ref_device = CFUNC(ct.POINTER(device),
    ct.POINTER(device))(
    ("libusb_ref_device", dll), (
    (1, "dev"),))

unref_device = CFUNC(None,
    ct.POINTER(device))(
    ("libusb_unref_device", dll), (
    (1, "dev"),))

get_configuration = CFUNC(ct.c_int,
    ct.POINTER(device_handle),
    ct.POINTER(ct.c_int))(
    ("libusb_get_configuration", dll), (
    (1, "dev_handle"),
    (1, "config"),))

get_device_descriptor = CFUNC(ct.c_int,
    ct.POINTER(device),
    ct.POINTER(device_descriptor))(
    ("libusb_get_device_descriptor", dll), (
    (1, "dev"),
    (1, "desc"),))

get_active_config_descriptor = CFUNC(ct.c_int,
    ct.POINTER(device),
    ct.POINTER(ct.POINTER(config_descriptor)))(
    ("libusb_get_active_config_descriptor", dll), (
    (1, "dev"),
    (1, "config"),))

get_config_descriptor = CFUNC(ct.c_int,
    ct.POINTER(device),
    ct.c_uint8,
    ct.POINTER(ct.POINTER(config_descriptor)))(
    ("libusb_get_config_descriptor", dll), (
    (1, "dev"),
    (1, "config_index"),
    (1, "config"),))

get_config_descriptor_by_value = CFUNC(ct.c_int,
    ct.POINTER(device),
    ct.c_uint8,
    ct.POINTER(ct.POINTER(config_descriptor)))(
    ("libusb_get_config_descriptor_by_value", dll), (
    (1, "dev"),
    (1, "bConfigurationValue"),
    (1, "config"),))

free_config_descriptor = CFUNC(None,
    ct.POINTER(config_descriptor))(
    ("libusb_free_config_descriptor", dll), (
    (1, "config"),))

get_ss_endpoint_companion_descriptor = CFUNC(ct.c_int,
    ct.POINTER(context),
    ct.POINTER(endpoint_descriptor),
    ct.POINTER(ct.POINTER(ss_endpoint_companion_descriptor)))(
    ("libusb_get_ss_endpoint_companion_descriptor", dll), (
    (1, "ctx"),
    (1, "endpoint"),
    (1, "ep_comp"),))

free_ss_endpoint_companion_descriptor = CFUNC(None,
    ct.POINTER(ss_endpoint_companion_descriptor))(
    ("libusb_free_ss_endpoint_companion_descriptor", dll), (
    (1, "ep_comp"),))

get_bos_descriptor = CFUNC(ct.c_int,
    ct.POINTER(device_handle),
    ct.POINTER(ct.POINTER(bos_descriptor)))(
    ("libusb_get_bos_descriptor", dll), (
    (1, "dev_handle"),
    (1, "bos"),))

free_bos_descriptor = CFUNC(None,
    ct.POINTER(bos_descriptor))(
    ("libusb_free_bos_descriptor", dll), (
    (1, "bos"),))

get_usb_2_0_extension_descriptor = CFUNC(ct.c_int,
    ct.POINTER(context),
    ct.POINTER(bos_dev_capability_descriptor),
    ct.POINTER(ct.POINTER(usb_2_0_extension_descriptor)))(
    ("libusb_get_usb_2_0_extension_descriptor", dll), (
    (1, "ctx"),
    (1, "dev_cap"),
    (1, "usb_2_0_extension"),))

free_usb_2_0_extension_descriptor = CFUNC(None,
    ct.POINTER(usb_2_0_extension_descriptor))(
    ("libusb_free_usb_2_0_extension_descriptor", dll), (
    (1, "usb_2_0_extension"),))

get_ss_usb_device_capability_descriptor = CFUNC(ct.c_int,
    ct.POINTER(context),
    ct.POINTER(bos_dev_capability_descriptor),
    ct.POINTER(ct.POINTER(ss_usb_device_capability_descriptor)))(
    ("libusb_get_ss_usb_device_capability_descriptor", dll), (
    (1, "ctx"),
    (1, "dev_cap"),
    (1, "ss_usb_device_cap"),))

free_ss_usb_device_capability_descriptor = CFUNC(None,
    ct.POINTER(ss_usb_device_capability_descriptor))(
    ("libusb_free_ss_usb_device_capability_descriptor", dll), (
    (1, "ss_usb_device_cap"),))

get_container_id_descriptor = CFUNC(ct.c_int,
    ct.POINTER(context),
    ct.POINTER(bos_dev_capability_descriptor),
    ct.POINTER(ct.POINTER(container_id_descriptor)))(
    ("libusb_get_container_id_descriptor", dll), (
    (1, "ctx"),
    (1, "dev_cap"),
    (1, "container_id"),))

free_container_id_descriptor = CFUNC(None,
    ct.POINTER(container_id_descriptor))(
    ("libusb_free_container_id_descriptor", dll), (
    (1, "container_id"),))

try:
    get_platform_descriptor = CFUNC(ct.c_int,
        ct.POINTER(context),
        ct.POINTER(bos_dev_capability_descriptor),
        ct.POINTER(ct.POINTER(platform_descriptor)))(
        ("libusb_get_platform_descriptor", dll), (
        (1, "ctx"),
        (1, "dev_cap"),
        (1, "platform_descriptor"),))

    free_platform_descriptor = CFUNC(None,
        ct.POINTER(platform_descriptor))(
        ("libusb_free_platform_descriptor", dll), (
        (1, "platform_descriptor"),))
except: pass  # noqa: E722

get_bus_number = CFUNC(ct.c_uint8,
    ct.POINTER(device))(
    ("libusb_get_bus_number", dll), (
    (1, "dev"),))

get_port_number = CFUNC(ct.c_uint8,
    ct.POINTER(device))(
    ("libusb_get_port_number", dll), (
    (1, "dev"),))

get_port_numbers = CFUNC(ct.c_int,
    ct.POINTER(device),
    ct.POINTER(ct.c_uint8),
    ct.c_int)(
    ("libusb_get_port_numbers", dll), (
    (1, "dev"),
    (1, "port_numbers"),
    (1, "port_numbers_len"),))
LIBUSB_DEPRECATED_FOR("get_port_numbers")

get_port_path = CFUNC(ct.c_int,
    ct.POINTER(context),
    ct.POINTER(device),
    ct.POINTER(ct.c_uint8),
    ct.c_uint8)(
    ("libusb_get_port_path", dll), (
    (1, "ctx"),
    (1, "dev"),
    (1, "path"),
    (1, "path_length"),))

get_parent = CFUNC(ct.POINTER(device),
    ct.POINTER(device))(
    ("libusb_get_parent", dll), (
    (1, "dev"),))

get_device_address = CFUNC(ct.c_uint8,
    ct.POINTER(device))(
    ("libusb_get_device_address", dll), (
    (1, "dev"),))

get_device_speed = CFUNC(ct.c_int,
    ct.POINTER(device))(
    ("libusb_get_device_speed", dll), (
    (1, "dev"),))

get_max_packet_size = CFUNC(ct.c_int,
    ct.POINTER(device),
    ct.c_ubyte)(
    ("libusb_get_max_packet_size", dll), (
    (1, "dev"),
    (1, "endpoint"),))

get_max_iso_packet_size = CFUNC(ct.c_int,
    ct.POINTER(device),
    ct.c_ubyte)(
    ("libusb_get_max_iso_packet_size", dll), (
    (1, "dev"),
    (1, "endpoint"),))

try:
    get_max_alt_packet_size = CFUNC(ct.c_int,
        ct.POINTER(device),
        ct.c_int,
        ct.c_int,
        ct.c_ubyte)(
        ("libusb_get_max_alt_packet_size", dll), (
        (1, "dev"),
        (1, "interface_number"),
        (1, "alternate_setting"),
        (1, "endpoint"),))
except: pass  # noqa: E722

try:
    get_interface_association_descriptors = CFUNC(ct.c_int,
        ct.POINTER(device),
        ct.c_uint8,
        ct.POINTER(ct.POINTER(interface_association_descriptor_array)))(
        ("libusb_get_interface_association_descriptors", dll), (
        (1, "dev"),
        (1, "config_index"),
        (1, "iad_array"),))

    get_active_interface_association_descriptors = CFUNC(ct.c_int,
        ct.POINTER(device),
        ct.POINTER(ct.POINTER(interface_association_descriptor_array)))(
        ("libusb_get_active_interface_association_descriptors", dll), (
        (1, "dev"),
        (1, "iad_array"),))

    free_interface_association_descriptors = CFUNC(None,
        ct.POINTER(interface_association_descriptor_array))(
        ("libusb_free_interface_association_descriptors", dll), (
        (1, "iad_array"),))
except: pass  # noqa: E722

try:
    wrap_sys_device = CFUNC(ct.c_int,
        ct.POINTER(context),
        intptr_t,
        ct.POINTER(ct.POINTER(device_handle)))(
        ("libusb_wrap_sys_device", dll), (
        (1, "ctx"),
        (1, "sys_dev"),
        (1, "dev_handle"),))
except: pass  # noqa: E722

open = CFUNC(ct.c_int,  # noqa: A001
    ct.POINTER(device),
    ct.POINTER(ct.POINTER(device_handle)))(
    ("libusb_open", dll), (
    (1, "dev"),
    (1, "dev_handle"),))

close = CFUNC(None,
    ct.POINTER(device_handle))(
    ("libusb_close", dll), (
    (1, "dev_handle"),))

get_device = CFUNC(ct.POINTER(device),
    ct.POINTER(device_handle))(
    ("libusb_get_device", dll), (
    (1, "dev_handle"),))

set_configuration = CFUNC(ct.c_int,
    ct.POINTER(device_handle), ct.c_int)(
    ("libusb_set_configuration", dll), (
    (1, "dev_handle"),
    (1, "configuration"),))

claim_interface = CFUNC(ct.c_int,
    ct.POINTER(device_handle), ct.c_int)(
    ("libusb_claim_interface", dll), (
    (1, "dev_handle"),
    (1, "interface_number"),))

release_interface = CFUNC(ct.c_int,
    ct.POINTER(device_handle), ct.c_int)(
    ("libusb_release_interface", dll), (
    (1, "dev_handle"),
    (1, "interface_number"),))

open_device_with_vid_pid = CFUNC(ct.POINTER(device_handle),
    ct.POINTER(context),
    ct.c_uint16,
    ct.c_uint16)(
    ("libusb_open_device_with_vid_pid", dll), (
    (1, "ctx"),
    (1, "vendor_id"),
    (1, "product_id"),))

set_interface_alt_setting = CFUNC(ct.c_int,
    ct.POINTER(device_handle),
    ct.c_int,
    ct.c_int)(
    ("libusb_set_interface_alt_setting", dll), (
    (1, "dev_handle"),
    (1, "interface_number"),
    (1, "alternate_setting"),))

clear_halt = CFUNC(ct.c_int,
    ct.POINTER(device_handle),
    ct.c_ubyte)(
    ("libusb_clear_halt", dll), (
    (1, "dev_handle"),
    (1, "endpoint"),))

reset_device = CFUNC(ct.c_int,
    ct.POINTER(device_handle))(
    ("libusb_reset_device", dll), (
    (1, "dev_handle"),))

alloc_streams = CFUNC(ct.c_int,
    ct.POINTER(device_handle),
    ct.c_uint32,
    ct.POINTER(ct.c_ubyte),
    ct.c_int)(
    ("libusb_alloc_streams", dll), (
    (1, "dev_handle"),
    (1, "num_streams"),
    (1, "endpoints"),
    (1, "num_endpoints"),))

free_streams = CFUNC(ct.c_int,
    ct.POINTER(device_handle),
    ct.POINTER(ct.c_ubyte),
    ct.c_int)(
    ("libusb_free_streams", dll), (
    (1, "dev_handle"),
    (1, "endpoints"),
    (1, "num_endpoints"),))

dev_mem_alloc = CFUNC(ct.POINTER(ct.c_ubyte),
    ct.POINTER(device_handle),
    ct.c_size_t)(
    ("libusb_dev_mem_alloc", dll), (
    (1, "dev_handle"),
    (1, "length"),))

dev_mem_free = CFUNC(ct.c_int,
    ct.POINTER(device_handle),
    ct.POINTER(ct.c_ubyte),
    ct.c_size_t)(
    ("libusb_dev_mem_free", dll), (
    (1, "dev_handle"),
    (1, "buffer"),
    (1, "length"),))

kernel_driver_active = CFUNC(ct.c_int,
    ct.POINTER(device_handle),
    ct.c_int)(
    ("libusb_kernel_driver_active", dll), (
    (1, "dev_handle"),
    (1, "interface_number"),))

detach_kernel_driver = CFUNC(ct.c_int,
    ct.POINTER(device_handle),
    ct.c_int)(
    ("libusb_detach_kernel_driver", dll), (
    (1, "dev_handle"),
    (1, "interface_number"),))

attach_kernel_driver = CFUNC(ct.c_int,
    ct.POINTER(device_handle),
    ct.c_int)(
    ("libusb_attach_kernel_driver", dll), (
    (1, "dev_handle"),
    (1, "interface_number"),))

set_auto_detach_kernel_driver = CFUNC(ct.c_int,
    ct.POINTER(device_handle),
    ct.c_int)(
    ("libusb_set_auto_detach_kernel_driver", dll), (
    (1, "dev_handle"),
    (1, "enable"),))

## async I/O ##

# \ingroup libusb::asyncio
# Get the data section of a control transfer. This convenience function is here
# to remind you that the data does not start until 8 bytes into the actual
# buffer, as the setup packet comes first.
#
# Calling this function only makes sense from a transfer callback function,
# or situations where you have already allocated a suitably sized buffer at
# transfer->buffer.
#
# :param transfer: a transfer
# :returns: pointer to the first byte of the data section

# static inline
# @CFUNC(ct.POINTER(ct.c_ubyte), ct.POINTER(transfer))
def control_transfer_get_data(transfer):
    transfer = transfer[0]
    return ct.cast(transfer.buffer + LIBUSB_CONTROL_SETUP_SIZE, ct.POINTER(ct.c_ubyte))

# \ingroup libusb::asyncio
# Get the control setup packet of a control transfer. This convenience
# function is here to remind you that the control setup occupies the first
# 8 bytes of the transfer data buffer.
#
# Calling this function only makes sense from a transfer callback function,
# or situations where you have already allocated a suitably sized buffer at
# transfer->buffer.
#
# :param transfer: a transfer
# :returns: a casted pointer to the start of the transfer data buffer

# static inline
# @CFUNC(ct.POINTER(control_setup), ct.POINTER(transfer))
def control_transfer_get_setup(transfer):
    transfer = transfer[0]
    return ct.cast(transfer.buffer, ct.POINTER(control_setup))

# \ingroup libusb::asyncio
# Helper function to populate the setup packet (first 8 bytes of the data
# buffer) for a control transfer. The wIndex, wValue and wLength values should
# be given in host-endian byte order.
#
# :param buffer: buffer to output the setup packet into
# This pointer must be aligned to at least 2 bytes boundary.
# :param bmRequestType: see the
# \ref libusb.control_setup::bmRequestType "bmRequestType" field of
# \ref libusb.control_setup
# :param bRequest: see the
# \ref libusb.control_setup::bRequest "bRequest" field of
# \ref libusb.control_setup
# :param wValue: see the
# \ref libusb.control_setup::wValue "wValue" field of
# \ref libusb.control_setup
# :param wIndex: see the
# \ref libusb.control_setup::wIndex "wIndex" field of
# \ref libusb.control_setup
# :param wLength: see the
# \ref libusb.control_setup::wLength "wLength" field of
# \ref libusb.control_setup

# static inline
@CFUNC(None,
       ct.POINTER(ct.c_ubyte), ct.c_uint8,  ct.c_uint8,  ct.c_uint16, ct.c_uint16, ct.c_uint16)
def fill_control_setup(buffer, bmRequestType, bRequest, wValue, wIndex, wLength):
    setup = ct.cast(buffer, ct.POINTER(control_setup))[0]
    setup.bmRequestType = bmRequestType
    setup.bRequest      = bRequest
    setup.wValue        = cpu_to_le16(wValue)
    setup.wIndex        = cpu_to_le16(wIndex)
    setup.wLength       = cpu_to_le16(wLength)

alloc_transfer = CFUNC(ct.POINTER(transfer),
    ct.c_int)(
    ("libusb_alloc_transfer", dll), (
    (1, "iso_packets"),))

submit_transfer = CFUNC(ct.c_int,
    ct.POINTER(transfer))(
    ("libusb_submit_transfer", dll), (
    (1, "transfer"),))

cancel_transfer = CFUNC(ct.c_int,
    ct.POINTER(transfer))(
    ("libusb_cancel_transfer", dll), (
    (1, "transfer"),))

free_transfer = CFUNC(None,
    ct.POINTER(transfer))(
    ("libusb_free_transfer", dll), (
    (1, "transfer"),))

transfer_get_stream_id = CFUNC(ct.c_uint32,
    ct.POINTER(transfer))(
    ("libusb_transfer_get_stream_id", dll), (
    (1, "transfer"),))

transfer_set_stream_id = CFUNC(None,
    ct.POINTER(transfer), ct.c_uint32)(
    ("libusb_transfer_set_stream_id", dll), (
    (1, "transfer"),
    (1, "stream_id"),))

# \ingroup libusb::asyncio
# Helper function to populate the required \ref libusb.transfer fields
# for a control transfer.
#
# If you pass a transfer buffer to this function, the first 8 bytes will
# be interpreted as a control setup packet, and the wLength field will be
# used to automatically populate the \ref libusb.transfer::length "length"
# field of the transfer. Therefore the recommended approach is:
# -# Allocate a suitably sized data buffer (including space for control setup)
# -# Call libusb.fill_control_setup()
# -# If this is a host-to-device transfer with a data stage, put the data
#    in place after the setup packet
# -# Call this function
# -# Call libusb.submit_transfer()
#
# It is also legal to pass a NULL buffer to this function, in which case this
# function will not attempt to populate the length field. Remember that you
# must then populate the buffer and length fields later.
#
# :param transfer: the transfer to populate
# :param dev_handle: handle of the device that will handle the transfer
# :param buffer: data buffer. If provided, this function will interpret the
# first 8 bytes as a setup packet and infer the transfer length from that.
# This pointer must be aligned to at least 2 bytes boundary.
# :param callback: callback function to be invoked on transfer completion
# :param user_data: user data to pass to callback function
# :param timeout: timeout for the transfer in milliseconds

# static inline
@CFUNC(None,
       ct.POINTER(transfer), ct.POINTER(device_handle),
       ct.POINTER(ct.c_ubyte), transfer_cb_fn, ct.c_void_p, ct.c_uint)
def fill_control_transfer(transfer, dev_handle, buffer, callback, user_data, timeout):
    transfer  = transfer[0]
    setup_ptr = ct.cast(buffer, ct.POINTER(control_setup))
    transfer.dev_handle = dev_handle
    transfer.endpoint   = 0
    transfer.type       = LIBUSB_TRANSFER_TYPE_CONTROL
    transfer.timeout    = timeout
    transfer.buffer     = buffer
    if setup_ptr:
        transfer.length = ct.c_int(LIBUSB_CONTROL_SETUP_SIZE + le16_to_cpu(setup_ptr[0].wLength))
    transfer.user_data  = user_data
    transfer.callback   = callback

# \ingroup libusb::asyncio
# Helper function to populate the required \ref libusb.transfer fields
# for a bulk transfer.
#
# :param transfer: the transfer to populate
# :param dev_handle: handle of the device that will handle the transfer
# :param endpoint: address of the endpoint where this transfer will be sent
# :param buffer: data buffer
# :param length: length of data buffer
# :param callback: callback function to be invoked on transfer completion
# :param user_data: user data to pass to callback function
# :param timeout: timeout for the transfer in milliseconds

# static inline
@CFUNC(None,
       ct.POINTER(transfer), ct.POINTER(device_handle), ct.c_ubyte,
       ct.POINTER(ct.c_ubyte), ct.c_int, transfer_cb_fn, ct.c_void_p, ct.c_uint)
def fill_bulk_transfer(transfer, dev_handle, endpoint,
                       buffer, length, callback, user_data, timeout):
    transfer = transfer[0]
    transfer.dev_handle = dev_handle
    transfer.endpoint   = endpoint
    transfer.type       = LIBUSB_TRANSFER_TYPE_BULK
    transfer.timeout    = timeout
    transfer.buffer     = buffer
    transfer.length     = length
    transfer.user_data  = user_data
    transfer.callback   = callback

# \ingroup libusb::asyncio
# Helper function to populate the required \ref libusb.transfer fields
# for a bulk transfer using bulk streams.
#
# Since version 1.0.19, \ref LIBUSB_API_VERSION >= 0x01000103
#
# :param transfer: the transfer to populate
# :param dev_handle: handle of the device that will handle the transfer
# :param endpoint: address of the endpoint where this transfer will be sent
# :param stream_id: bulk stream id for this transfer
# :param buffer: data buffer
# :param length: length of data buffer
# :param callback: callback function to be invoked on transfer completion
# :param user_data: user data to pass to callback function
# :param timeout: timeout for the transfer in milliseconds

# static inline
@CFUNC(None,
       ct.POINTER(transfer), ct.POINTER(device_handle), ct.c_ubyte, ct.c_uint32,
       ct.POINTER(ct.c_ubyte), ct.c_int, transfer_cb_fn, ct.c_void_p, ct.c_uint)
def fill_bulk_stream_transfer(transfer, dev_handle, endpoint, stream_id,
                              buffer, length, callback, user_data, timeout):
    fill_bulk_transfer(transfer, dev_handle, endpoint,
                       buffer, length, callback, user_data, timeout)
    transfer[0].type = LIBUSB_TRANSFER_TYPE_BULK_STREAM
    transfer_set_stream_id(transfer, stream_id)

# \ingroup libusb::asyncio
# Helper function to populate the required \ref libusb.transfer fields
# for an interrupt transfer.
#
# :param transfer: the transfer to populate
# :param dev_handle: handle of the device that will handle the transfer
# :param endpoint: address of the endpoint where this transfer will be sent
# :param buffer: data buffer
# :param length: length of data buffer
# :param callback: callback function to be invoked on transfer completion
# :param user_data: user data to pass to callback function
# :param timeout: timeout for the transfer in milliseconds

# static inline
@CFUNC(None,
       ct.POINTER(transfer), ct.POINTER(device_handle), ct.c_ubyte,
       ct.POINTER(ct.c_ubyte), ct.c_int, transfer_cb_fn, ct.c_void_p, ct.c_uint)
def fill_interrupt_transfer(transfer, dev_handle, endpoint,
                            buffer, length, callback, user_data, timeout):
    transfer = transfer[0]
    transfer.dev_handle = dev_handle
    transfer.endpoint   = endpoint
    transfer.type       = LIBUSB_TRANSFER_TYPE_INTERRUPT
    transfer.timeout    = timeout
    transfer.buffer     = buffer
    transfer.length     = length
    transfer.user_data  = user_data
    transfer.callback   = callback

# \ingroup libusb::asyncio
# Helper function to populate the required \ref libusb.transfer fields
# for an isochronous transfer.
#
# :param transfer: the transfer to populate
# :param dev_handle: handle of the device that will handle the transfer
# :param endpoint: address of the endpoint where this transfer will be sent
# :param buffer: data buffer
# :param length: length of data buffer
# :param num_iso_packets: the number of isochronous packets
# :param callback: callback function to be invoked on transfer completion
# :param user_data: user data to pass to callback function
# :param timeout: timeout for the transfer in milliseconds

# static inline
@CFUNC(None,
       ct.POINTER(transfer), ct.POINTER(device_handle), ct.c_ubyte,
       ct.POINTER(ct.c_ubyte), ct.c_int, ct.c_int, transfer_cb_fn, ct.c_void_p, ct.c_uint)
def fill_iso_transfer(transfer, dev_handle, endpoint,
                      buffer, length, num_iso_packets, callback, user_data, timeout):
    transfer = transfer[0]
    transfer.dev_handle      = dev_handle
    transfer.endpoint        = endpoint
    transfer.type            = LIBUSB_TRANSFER_TYPE_ISOCHRONOUS
    transfer.timeout         = timeout
    transfer.buffer          = buffer
    transfer.length          = length
    transfer.num_iso_packets = num_iso_packets
    transfer.user_data       = user_data
    transfer.callback        = callback

# \ingroup libusb::asyncio
# Convenience function to set the length of all packets in an isochronous
# transfer, based on the num_iso_packets field in the transfer structure.
#
# :param transfer: a transfer
# :param length: the length to set in each isochronous packet descriptor
# \see libusb.get_max_packet_size()

# static inline
@CFUNC(None, ct.POINTER(transfer), ct.c_uint)
def set_iso_packet_lengths(transfer, length):
    transfer = transfer[0]
    for i in range(transfer.num_iso_packets):
        transfer.iso_packet_desc[i].length = length

# \ingroup libusb::asyncio
# Convenience function to locate the position of an isochronous packet
# within the buffer of an isochronous transfer.
#
# This is a thorough function which loops through all preceding packets,
# accumulating their lengths to find the position of the specified packet.
# Typically you will assign equal lengths to each packet in the transfer,
# and hence the above method is sub-optimal. You may wish to use
# libusb.get_iso_packet_buffer_simple() instead.
#
# :param transfer: a transfer
# :param packet: the packet to return the address of
# :returns: the base address of the packet buffer inside the transfer buffer,
# or NULL if the packet does not exist.
# \see libusb.get_iso_packet_buffer_simple()

# static inline
# @CFUNC(ct.POINTER(ct.c_ubyte), ct.POINTER(transfer), ct.c_uint)
def get_iso_packet_buffer(transfer, packet):
    packet = packet.value

    # oops..slight bug in the API. packet is an unsigned int, but we use
    # signed integers almost everywhere else. range-check and convert to
    # signed to avoid compiler warnings. FIXME for libusb-2.
    if packet > INT_MAX:
        return None

    transfer = transfer[0]

    if packet >= transfer.num_iso_packets:
        return None

    offset = 0
    for i in range(packet):
        offset += transfer.iso_packet_desc[i].length

    return ct.cast(transfer.buffer + offset, ct.POINTER(ct.c_ubyte))

# \ingroup libusb::asyncio
# Convenience function to locate the position of an isochronous packet
# within the buffer of an isochronous transfer, for transfers where each
# packet is of identical size.
#
# This function relies on the assumption that every packet within the transfer
# is of identical size to the first packet. Calculating the location of
# the packet buffer is then just a simple calculation:
# <tt>buffer + (packet_size# packet)</tt>
#
# Do not use this function on transfers other than those that have identical
# packet lengths for each packet.
#
# :param transfer: a transfer
# :param packet: the packet to return the address of
# :returns: the base address of the packet buffer inside the transfer buffer,
# or NULL if the packet does not exist.
# \see libusb.get_iso_packet_buffer()

# static inline
# @CFUNC(ct.POINTER(ct.c_ubyte), ct.POINTER(transfer), ct.c_uint)
def get_iso_packet_buffer_simple(transfer, packet):
    packet = packet.value

    # oops..slight bug in the API. packet is an unsigned int, but we use
    # signed integers almost everywhere else. range-check and convert to
    # signed to avoid compiler warnings. FIXME for libusb-2.
    if packet > INT_MAX:
        return None

    transfer = transfer[0]

    if packet >= transfer.num_iso_packets:
        return None

    return ct.cast(transfer.buffer
                   + ct.c_int(transfer.iso_packet_desc[0].length).value * packet,
                   ct.POINTER(ct.c_ubyte))

## sync I/O ##

control_transfer = CFUNC(ct.c_int,
    ct.POINTER(device_handle),
    ct.c_uint8,
    ct.c_uint8,
    ct.c_uint16,
    ct.c_uint16,
    ct.POINTER(ct.c_ubyte),
    ct.c_uint16,
    ct.c_uint)(
    ("libusb_control_transfer", dll), (
    (1, "dev_handle"),
    (1, "request_type"),
    (1, "bRequest"),
    (1, "wValue"),
    (1, "wIndex"),
    (1, "data"),
    (1, "wLength"),
    (1, "timeout"),))

bulk_transfer = CFUNC(ct.c_int,
    ct.POINTER(device_handle),
    ct.c_ubyte,
    ct.POINTER(ct.c_ubyte),
    ct.c_int,
    ct.POINTER(ct.c_int),
    ct.c_uint)(
    ("libusb_bulk_transfer", dll), (
    (1, "dev_handle"),
    (1, "endpoint"),
    (1, "data"),
    (1, "length"),
    (1, "actual_length"),
    (1, "timeout"),))

interrupt_transfer = CFUNC(ct.c_int,
    ct.POINTER(device_handle),
    ct.c_ubyte,
    ct.POINTER(ct.c_ubyte),
    ct.c_int,
    ct.POINTER(ct.c_int),
    ct.c_uint)(
    ("libusb_interrupt_transfer", dll), (
    (1, "dev_handle"),
    (1, "endpoint"),
    (1, "data"),
    (1, "length"),
    (1, "actual_length"),
    (1, "timeout"),))

# \ingroup libusb::desc
# Retrieve a descriptor from the default control pipe.
# This is a convenience function which formulates the appropriate control
# message to retrieve the descriptor.
#
# :param dev_handle: a device handle
# :param desc_type: the descriptor type, see \ref libusb.descriptor_type
# :param desc_index: the index of the descriptor to retrieve
# :param data: output buffer for descriptor
# :param length: size of data buffer
# :returns: number of bytes returned in data, or LIBUSB_ERROR code on failure

# static inline
@CFUNC(ct.c_int,
       ct.POINTER(device_handle), ct.c_uint8, ct.c_uint8, ct.POINTER(ct.c_ubyte), ct.c_int)
def get_descriptor(dev_handle, desc_type, desc_index, data, length):
    return control_transfer(dev_handle,
                            LIBUSB_ENDPOINT_IN, LIBUSB_REQUEST_GET_DESCRIPTOR,
                            ct.c_uint16((desc_type << 8) | desc_index),
                            0, data, ct.c_uint16(length), 1000)

# \ingroup libusb::desc
# Retrieve a descriptor from a device.
# This is a convenience function which formulates the appropriate control
# message to retrieve the descriptor. The string returned is Unicode, as
# detailed in the USB specifications.
#
# :param dev_handle: a device handle
# :param desc_index: the index of the descriptor to retrieve
# :param langid: the language ID for the string descriptor
# :param data: output buffer for descriptor
# :param length: size of data buffer
# :returns: number of bytes returned in data, or LIBUSB_ERROR code on failure
# \see libusb.get_string_descriptor_ascii()

# static inline
@CFUNC(ct.c_int,
       ct.POINTER(device_handle), ct.c_uint8, ct.c_uint16, ct.POINTER(ct.c_ubyte), ct.c_int)
def get_string_descriptor(dev_handle, desc_index, langid, data, length):
    return control_transfer(dev_handle,
                            LIBUSB_ENDPOINT_IN, LIBUSB_REQUEST_GET_DESCRIPTOR,
                            ct.c_uint16((LIBUSB_DT_STRING << 8) | desc_index),
                            langid, data, ct.c_uint16(length), 1000)

get_string_descriptor_ascii = CFUNC(ct.c_int,
    ct.POINTER(device_handle),
    ct.c_uint8,
    ct.POINTER(ct.c_ubyte),
    ct.c_int)(
    ("libusb_get_string_descriptor_ascii", dll), (
    (1, "dev_handle"),
    (1, "desc_index"),
    (1, "data"),
    (1, "length"),))

# polling and timeouts #

try_lock_events = CFUNC(ct.c_int,
    ct.POINTER(context))(
    ("libusb_try_lock_events", dll), (
    (1, "ctx"),))

lock_events = CFUNC(None,
    ct.POINTER(context))(
    ("libusb_lock_events", dll), (
    (1, "ctx"),))

unlock_events = CFUNC(None,
    ct.POINTER(context))(
    ("libusb_unlock_events", dll), (
    (1, "ctx"),))

event_handling_ok = CFUNC(ct.c_int,
    ct.POINTER(context))(
    ("libusb_event_handling_ok", dll), (
    (1, "ctx"),))

event_handler_active = CFUNC(ct.c_int,
    ct.POINTER(context))(
    ("libusb_event_handler_active", dll), (
    (1, "ctx"),))

interrupt_event_handler = CFUNC(None,
    ct.POINTER(context))(
    ("libusb_interrupt_event_handler", dll), (
    (1, "ctx"),))

lock_event_waiters = CFUNC(None,
    ct.POINTER(context))(
    ("libusb_lock_event_waiters", dll), (
    (1, "ctx"),))

unlock_event_waiters = CFUNC(None,
    ct.POINTER(context))(
    ("libusb_unlock_event_waiters", dll), (
    (1, "ctx"),))

wait_for_event = CFUNC(ct.c_int,
    ct.POINTER(context),
    ct.POINTER(timeval))(
    ("libusb_wait_for_event", dll), (
    (1, "ctx"),
    (1, "tv"),))

handle_events_timeout = CFUNC(ct.c_int,
    ct.POINTER(context),
    ct.POINTER(timeval))(
    ("libusb_handle_events_timeout", dll), (
    (1, "ctx"),
    (1, "tv"),))

handle_events_timeout_completed = CFUNC(ct.c_int,
    ct.POINTER(context),
    ct.POINTER(timeval),
    ct.POINTER(ct.c_int))(
    ("libusb_handle_events_timeout_completed", dll), (
    (1, "ctx"),
    (1, "tv"),
    (1, "completed"),))

handle_events = CFUNC(ct.c_int,
    ct.POINTER(context))(
    ("libusb_handle_events", dll), (
    (1, "ctx"),))

handle_events_completed = CFUNC(ct.c_int,
    ct.POINTER(context),
    ct.POINTER(ct.c_int))(
    ("libusb_handle_events_completed", dll), (
    (1, "ctx"),
    (1, "completed"),))

handle_events_locked = CFUNC(ct.c_int,
    ct.POINTER(context),
    ct.POINTER(timeval))(
    ("libusb_handle_events_locked", dll), (
    (1, "ctx"),
    (1, "tv"),))

pollfds_handle_timeouts = CFUNC(ct.c_int,
    ct.POINTER(context))(
    ("libusb_pollfds_handle_timeouts", dll), (
    (1, "ctx"),))

get_next_timeout = CFUNC(ct.c_int,
    ct.POINTER(context),
    ct.POINTER(timeval))(
    ("libusb_get_next_timeout", dll), (
    (1, "ctx"),
    (1, "tv"),))

# \ingroup libusb::poll
# File descriptor for polling

class pollfd(ct.Structure):
    _fields_ = [

    # Numeric file descriptor
    ("fd", ct.c_int),

    # Event flags to poll for from <poll.h>. POLLIN indicates that you
    # should monitor this file descriptor for becoming ready to read from,
    # and POLLOUT indicates that you should monitor this file descriptor for
    # nonblocking write readiness.
    ("events", ct.c_short),
]

# \ingroup libusb::poll
# Callback function, invoked when a new file descriptor should be added
# to the set of file descriptors monitored for events.
# :param fd: the new file descriptor
# :param events: events to monitor for, see \ref libusb.pollfd for a
# description
# :param user_data: User data pointer specified in
# libusb.set_pollfd_notifiers() call
# \see libusb.set_pollfd_notifiers()

pollfd_added_cb = CFUNC(None, ct.c_int, ct.c_short, ct.c_void_p)

# \ingroup libusb::poll
# Callback function, invoked when a file descriptor should be removed from
# the set of file descriptors being monitored for events. After returning
# from this callback, do not use that file descriptor again.
# :param fd: the file descriptor to stop monitoring
# :param user_data: User data pointer specified in
# libusb.set_pollfd_notifiers() call
# \see libusb.set_pollfd_notifiers()

pollfd_removed_cb = CFUNC(None, ct.c_int, ct.c_void_p)

get_pollfds = CFUNC(ct.POINTER(ct.POINTER(pollfd)),
    ct.POINTER(context))(
    ("libusb_get_pollfds", dll), (
    (1, "ctx"),))

free_pollfds = CFUNC(None,
    ct.POINTER(ct.POINTER(pollfd)))(
    ("libusb_free_pollfds", dll), (
    (1, "pollfds"),))

set_pollfd_notifiers = CFUNC(None,
    ct.POINTER(context),
    pollfd_added_cb,
    pollfd_removed_cb,
    ct.c_void_p)(
    ("libusb_set_pollfd_notifiers", dll), (
    (1, "ctx"),
    (1, "added_cb"),
    (1, "removed_cb"),
    (1, "user_data"),))

# \ingroup libusb::hotplug
# Callback handle.
#
# Callbacks handles are generated by libusb.hotplug_register_callback()
# and can be used to deregister callbacks. Callback handles are unique
# per libusb.context and it is safe to call libusb.hotplug_deregister_callback()
# on an already deregistered callback.
#
# Since version 1.0.16, \ref LIBUSB_API_VERSION >= 0x01000102
#
# For more information, see \ref libusb::hotplug.

hotplug_callback_handle = ct.c_int

# \ingroup libusb::hotplug
#
# Since version 1.0.16, \ref LIBUSB_API_VERSION >= 0x01000102
#
# Hotplug events
hotplug_event = ct.c_int
(
    # A device has been plugged in and is ready to use
    LIBUSB_HOTPLUG_EVENT_DEVICE_ARRIVED,

    # A device has left and is no longer available.
    # It is the user's responsibility to call libusb.close on any handle associated
    # with a disconnected device.
    # It is safe to call libusb.get_device_descriptor on a device that has left
    LIBUSB_HOTPLUG_EVENT_DEVICE_LEFT,

) = (1 << 0, 1 << 1)

# \ingroup libusb::hotplug
#
# Since version 1.0.16, \ref LIBUSB_API_VERSION >= 0x01000102
#
# Hotplug flags
hotplug_flag = ct.c_int
(
    # Arm the callback and fire it for all matching currently attached devices.
    LIBUSB_HOTPLUG_ENUMERATE,

) = (1 << 0,)

# \ingroup libusb::hotplug
# Convenience macro when not using any flags
LIBUSB_HOTPLUG_NO_FLAGS = 0

# \ingroup libusb::hotplug
# Wildcard matching for hotplug events
LIBUSB_HOTPLUG_MATCH_ANY = ct.c_int(-1)

# \ingroup libusb::hotplug
# Hotplug callback function type. When requesting hotplug event notifications,
# you pass a pointer to a callback function of this type.
#
# This callback may be called by an internal event thread and as such it is
# recommended the callback do minimal processing before returning.
#
# libusb will call this function later, when a matching event had happened on
# a matching device. See \ref libusb::hotplug for more information.
#
# It is safe to call either libusb.hotplug_register_callback() or
# libusb.hotplug_deregister_callback() from within a callback function.
#
# Since version 1.0.16, \ref LIBUSB_API_VERSION >= 0x01000102
#
# :param ctx:            context of this notification
# :param device:         libusb.device this event occurred on
# :param event:          event that occurred
# :param user_data:      user data provided when this callback was registered
# :returns: bool whether this callback is finished processing events.
#                        returning 1 will cause this callback to be deregistered

hotplug_callback_fn = CFUNC(ct.c_int,
    ct.POINTER(context),
    ct.POINTER(device),
    hotplug_event,
    ct.c_void_p)

# \ingroup libusb::hotplug
# Register a hotplug callback function
#
# Register a callback with the libusb.context. The callback will fire
# when a matching event occurs on a matching device. The callback is
# armed until either it is deregistered with libusb.hotplug_deregister_callback()
# or the supplied callback returns 1 to indicate it is finished processing events.
#
# If the \ref LIBUSB_HOTPLUG_ENUMERATE is passed the callback will be
# called with a \ref LIBUSB_HOTPLUG_EVENT_DEVICE_ARRIVED for all devices
# already plugged into the machine. Note that libusb modifies its internal
# device list from a separate thread, while calling hotplug callbacks from
# libusb.handle_events(), so it is possible for a device to already be present
# on, or removed from, its internal device list, while the hotplug callbacks
# still need to be dispatched. This means that when using \ref
# LIBUSB_HOTPLUG_ENUMERATE, your callback may be called twice for the arrival
# of the same device, once from libusb.hotplug_register_callback() and once
# from libusb.handle_events(); and/or your callback may be called for the
# removal of a device for which an arrived call was never made.
#
# Since version 1.0.16, \ref LIBUSB_API_VERSION >= 0x01000102
#
# :param ctx: context to register this callback with
# :param events: bitwise or of hotplug events that will trigger this callback.
#                See \ref libusb.hotplug_event
# :param flags: bitwise or of hotplug flags that affect registration.
#               See \ref libusb.hotplug_flag
# :param vendor_id: the vendor id to match or \ref libusb.LIBUSB_HOTPLUG_MATCH_ANY
# :param product_id: the product id to match or \ref libusb.LIBUSB_HOTPLUG_MATCH_ANY
# :param dev_class: the device class to match or \ref libusb.LIBUSB_HOTPLUG_MATCH_ANY
# :param cb_fn: the function to be invoked on a matching event/device
# :param user_data: user data to pass to the callback function
# \param[out] callback_handle pointer to store the handle of the allocated callback (can be NULL)
# :returns: \ref LIBUSB_SUCCESS on success LIBUSB_ERROR code on failure

hotplug_register_callback = CFUNC(ct.c_int,
    ct.POINTER(context),
    ct.c_int,
    ct.c_int,
    ct.c_int,
    ct.c_int,
    ct.c_int,
    hotplug_callback_fn,
    ct.c_void_p,
    ct.POINTER(hotplug_callback_handle))(
    ("libusb_hotplug_register_callback", dll), (
    (1, "ctx"),
    (1, "events"),
    (1, "flags"),
    (1, "vendor_id"),
    (1, "product_id"),
    (1, "dev_class"),
    (1, "cb_fn"),
    (1, "user_data"),
    (1, "callback_handle"),))

# \ingroup libusb::hotplug
# Deregisters a hotplug callback.
#
# Deregister a callback from a libusb.context. This function is safe to call from within
# a hotplug callback.
#
# Since version 1.0.16, \ref LIBUSB_API_VERSION >= 0x01000102
#
# :param ctx: context this callback is registered with
# :param callback_handle: the handle of the callback to deregister

hotplug_deregister_callback = CFUNC(None,
    ct.POINTER(context),
    hotplug_callback_handle)(
    ("libusb_hotplug_deregister_callback", dll), (
    (1, "ctx"),
    (1, "callback_handle"),))

# \ingroup libusb::hotplug
# Gets the user_data associated with a hotplug callback.
#
# Since version v1.0.24 \ref LIBUSB_API_VERSION >= 0x01000108
#
# :param ctx: context this callback is registered with
# :param callback_handle: the handle of the callback to get the user_data of

try:
    hotplug_get_user_data = CFUNC(ct.c_void_p,
        ct.POINTER(context),
        hotplug_callback_handle)(
        ("libusb_hotplug_get_user_data", dll), (
        (1, "ctx"),
        (1, "callback_handle"),))
except: pass  # noqa: E722

_set_option_int = CFUNC(ct.c_int,
    ct.POINTER(context),
    option,
    ct.c_int)(
    ("libusb_set_option", dll), (
    (1, "ctx"),
    (1, "option"),
    (1, "value"),))

_set_option_log_cb = CFUNC(ct.c_int,
    ct.POINTER(context),
    option,
    log_cb)(
    ("libusb_set_option", dll), (
    (1, "ctx"),
    (1, "option"),
    (1, "value"),))

def set_option(ctx, option, *values):  # LIBUSB_CALLV
    if option == LIBUSB_OPTION_LOG_LEVEL:
        return _set_option_int(ctx, option, values[0])
    elif option == LIBUSB_OPTION_LOG_CB:
        return _set_option_log_cb(ctx, option, values[0])
    elif option in [LIBUSB_OPTION_USE_USBDK,
                    LIBUSB_OPTION_NO_DEVICE_DISCOVERY]:
        return _set_option_int(ctx, option, 0)
    else:
        return _set_option_int(ctx, option, 0)

#if defined("ENABLE_LOGGING") and not defined("ENABLE_DEBUG_LOGGING"):
context._fields_ = [
    ("debug",       log_level),
    ("debug_fixed", ct.c_int),
    ("log_handler", log_cb),
]
#endif

del defined

# eof
