# SPDX-License-Identifier: GPL-2.0+ WITH Linux-syscall-note
# *************************************************************************** #

# usbdevice_fs.h  --  USB device file system.
#
# Copyright (C) 2000
#       Thomas Sailer (sailer@ife.ee.ethz.ch)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# History:
#  0.1  04.01.2000  Created

# *************************************************************************** #

import ctypes as ct

#include <linux/types.h>
#include <linux/magic.h>
from ioctl_opt import IOC_READ, IOC_WRITE, IOC, IO, IOR, IOW, IOWR

c_uvoid_p = ct.c_void_p  # void __user *

# --------------------------------------------------------------------- #

# usbdevfs ioctl codes

class usbdevfs_ctrltransfer(ct.Structure):
    _fields_ = [
    ("bRequestType", ct.c_uint8),
    ("bRequest",     ct.c_uint8),
    ("wValue",       ct.c_uint16),
    ("wIndex",       ct.c_uint16),
    ("wLength",      ct.c_uint16),
    ("timeout",      ct.c_uint32),  # in milliseconds
    ("data",         c_uvoid_p),
]

class usbdevfs_bulktransfer(ct.Structure):
    _fields_ = [
    ("ep",      ct.c_uint),
    ("len",     ct.c_uint),
    ("timeout", ct.c_uint),  # in milliseconds
    ("data",    c_uvoid_p),
]

class usbdevfs_setinterface(ct.Structure):
    _fields_ = [
    ("interface",  ct.c_uint),
    ("altsetting", ct.c_uint),
]

class usbdevfs_disconnectsignal(ct.Structure):
    _fields_ = [
    ("signr",   ct.c_uint),
    ("context", c_uvoid_p),
]

USBDEVFS_MAXDRIVERNAME = 255

class usbdevfs_getdriver(ct.Structure):
    _fields_ = [
    ("interface", ct.c_uint),
    ("driver",    (ct.c_char * (USBDEVFS_MAXDRIVERNAME + 1))),
]

class usbdevfs_connectinfo(ct.Structure):
    _fields_ = [
    ("devnum", ct.c_uint),
    ("slow",   ct.c_ubyte),
]

class usbdevfs_conninfo_ex(ct.Structure):
    _fields_ = [
    ("size",      ct.c_uint32),   # Size of the structure from the kernel's
                                  # point of view. Can be used by userspace
                                  # to determine how much data can be
                                  # used/trusted.
    ("busnum",    ct.c_uint32),   # USB bus number, as enumerated by the
                                  # kernel, the device is connected to.
    ("devnum",    ct.c_uint32),   # Device address on the bus.
    ("speed",     ct.c_uint32),   # USB_SPEED_* constants from ch9.h
    ("num_ports", ct.c_uint8),    # Number of ports the device is connected
                                  # to on the way to the root hub. It may
                                  # be bigger than size of 'ports' array so
                                  # userspace can detect overflows.
    ("ports", (ct.c_uint8 * 7)),  # List of ports on the way from the root
                                  # hub to the device. Current limit in
                                  # USB specification is 7 tiers (root hub,
                                  # 5 intermediate hubs, device), which
                                  # gives at most 6 port entries.
]

USBDEVFS_URB_SHORT_NOT_OK      = 0x01
USBDEVFS_URB_ISO_ASAP          = 0x02
USBDEVFS_URB_BULK_CONTINUATION = 0x04
USBDEVFS_URB_NO_FSBR           = 0x20  # Not used
USBDEVFS_URB_ZERO_PACKET       = 0x40
USBDEVFS_URB_NO_INTERRUPT      = 0x80

USBDEVFS_URB_TYPE_ISO       = 0
USBDEVFS_URB_TYPE_INTERRUPT = 1
USBDEVFS_URB_TYPE_CONTROL   = 2
USBDEVFS_URB_TYPE_BULK      = 3

class usbdevfs_iso_packet_desc(ct.Structure):
    _fields_ = [
    ("length",        ct.c_uint),
    ("actual_length", ct.c_uint),
    ("status",        ct.c_uint),
]

class usbdevfs_urb(ct.Structure):
    class _Stream(ct.Union):
        _fields_ = [
        ("number_of_packets", ct.c_int),   # Only used for isoc urbs
        ("stream_id",         ct.c_uint),  # Only used with bulk streams
    ]
    _anonymous_ = ("_stream",)
    _fields_ = [
    ("type",           ct.c_ubyte),
    ("endpoint",       ct.c_ubyte),
    ("status",         ct.c_int),
    ("flags",          ct.c_uint),
    ("buffer",         c_uvoid_p),
    ("buffer_length",  ct.c_int),
    ("actual_length",  ct.c_int),
    ("start_frame",    ct.c_int),
    ("_stream",        _Stream),
    ("error_count",    ct.c_int),
    ("signr",          ct.c_uint),  # signal to be sent on completion,
                                    # or 0 if none should be sent.
    ("usercontext",    c_uvoid_p),
    ("iso_frame_desc", (usbdevfs_iso_packet_desc * 0)),
]

# ioctls for talking directly to drivers
class usbdevfs_ioctl(ct.Structure):
    _fields_ = [
    ("ifno",       ct.c_int),   # interface 0..N ; negative numbers reserved
    ("ioctl_code", ct.c_int),   # MUST encode size + direction of data so the
                                # macros in <asm/ioctl.h> give correct values
    ("data",       c_uvoid_p),  # param buffer (in, or out)
]

# You can do most things with hubs just through control messages,
# except find out what device connects to what port.
class usbdevfs_hub_portinfo(ct.Structure):
    _fields_ = [
    ("nports", ct.c_byte),          # number of downstream ports in this hub
    ("port",   (ct.c_byte * 127)),  # e.g. port 3 connects to device 27
]

# System and bus capability flags
USBDEVFS_CAP_ZERO_PACKET           = 0x01
USBDEVFS_CAP_BULK_CONTINUATION     = 0x02
USBDEVFS_CAP_NO_PACKET_SIZE_LIM    = 0x04
USBDEVFS_CAP_BULK_SCATTER_GATHER   = 0x08
USBDEVFS_CAP_REAP_AFTER_DISCONNECT = 0x10
USBDEVFS_CAP_MMAP                  = 0x20
USBDEVFS_CAP_DROP_PRIVILEGES       = 0x40
USBDEVFS_CAP_CONNINFO_EX           = 0x80
USBDEVFS_CAP_SUSPEND               = 0x100

# USBDEVFS_DISCONNECT_CLAIM flags & struct

# disconnect-and-claim if the driver matches the driver field
USBDEVFS_DISCONNECT_CLAIM_IF_DRIVER     = 0x01
# disconnect-and-claim except when the driver matches the driver field
USBDEVFS_DISCONNECT_CLAIM_EXCEPT_DRIVER = 0x02

class usbdevfs_disconnect_claim(ct.Structure):
    _fields_ = [
    ("interface", ct.c_uint),
    ("flags",     ct.c_uint),
    ("driver",    (ct.c_char * (USBDEVFS_MAXDRIVERNAME + 1))),
]

class usbdevfs_streams(ct.Structure):
    _fields_ = [
    ("num_streams", ct.c_uint),  # Not used by USBDEVFS_FREE_STREAMS
    ("num_eps",     ct.c_uint),
    ("eps",         (ct.c_ubyte * 0)),
]

# USB_SPEED_* values returned by USBDEVFS_GET_SPEED are defined in
# linux/usb/ch9.h

USBDEVFS_CONTROL           = IOWR(ord("U"),  0, usbdevfs_ctrltransfer)
# USBDEVFS_CONTROL32       = IOWR(ord("U"),  0, usbdevfs_ctrltransfer32)
USBDEVFS_BULK              = IOWR(ord("U"),  2, usbdevfs_bulktransfer)
# USBDEVFS_BULK32          = IOWR(ord("U"),  2, usbdevfs_bulktransfer32)
USBDEVFS_RESETEP           = IOR(ord("U"),   3, ct.c_uint)
USBDEVFS_SETINTERFACE      = IOR(ord("U"),   4, usbdevfs_setinterface)
USBDEVFS_SETCONFIGURATION  = IOR(ord("U"),   5, ct.c_uint)
USBDEVFS_GETDRIVER         = IOW(ord("U"),   8, usbdevfs_getdriver)
USBDEVFS_SUBMITURB         = IOR(ord("U"),  10, usbdevfs_urb)
# USBDEVFS_SUBMITURB32     = IOR(ord("U"),  10, usbdevfs_urb32)
USBDEVFS_DISCARDURB        = IO(ord("U"),   11)
USBDEVFS_REAPURB           = IOW(ord("U"),  12, ct.c_void_p)
USBDEVFS_REAPURB32         = IOW(ord("U"),  12, ct.c_uint32)
USBDEVFS_REAPURBNDELAY     = IOW(ord("U"),  13, ct.c_void_p)
USBDEVFS_REAPURBNDELAY32   = IOW(ord("U"),  13, ct.c_uint32)
USBDEVFS_DISCSIGNAL        = IOR(ord("U"),  14, usbdevfs_disconnectsignal)
# USBDEVFS_DISCSIGNAL32    = IOR(ord("U"),  14, usbdevfs_disconnectsignal32)
USBDEVFS_CLAIMINTERFACE    = IOR(ord("U"),  15, ct.c_uint)
USBDEVFS_RELEASEINTERFACE  = IOR(ord("U"),  16, ct.c_uint)
USBDEVFS_CONNECTINFO       = IOW(ord("U"),  17, usbdevfs_connectinfo)
USBDEVFS_IOCTL             = IOWR(ord("U"), 18, usbdevfs_ioctl)
# USBDEVFS_IOCTL32         = IOWR(ord("U"), 18, usbdevfs_ioctl32)
USBDEVFS_HUB_PORTINFO      = IOR(ord("U"),  19, usbdevfs_hub_portinfo)
USBDEVFS_RESET             = IO(ord("U"),   20)
USBDEVFS_CLEAR_HALT        = IOR(ord("U"),  21, ct.c_uint)
USBDEVFS_DISCONNECT        = IO(ord("U"),   22)
USBDEVFS_CONNECT           = IO(ord("U"),   23)
USBDEVFS_CLAIM_PORT        = IOR(ord("U"),  24, ct.c_uint)
USBDEVFS_RELEASE_PORT      = IOR(ord("U"),  25, ct.c_uint)
USBDEVFS_GET_CAPABILITIES  = IOR(ord("U"),  26, ct.c_uint32)
USBDEVFS_DISCONNECT_CLAIM  = IOR(ord("U"),  27, usbdevfs_disconnect_claim)
USBDEVFS_ALLOC_STREAMS     = IOR(ord("U"),  28, usbdevfs_streams)
USBDEVFS_FREE_STREAMS      = IOR(ord("U"),  29, usbdevfs_streams)
USBDEVFS_DROP_PRIVILEGES   = IOW(ord("U"),  30, ct.c_uint32)
USBDEVFS_GET_SPEED         = IO(ord("U"),   31)
# Returns struct usbdevfs_conninfo_ex; length is variable to allow
# extending size of the data returned.
USBDEVFS_CONNINFO_EX      = lambda len, __IOC=IOC, __IOC_READ=IOC_READ: \
                                        __IOC(__IOC_READ, ord(b"U"), 32, len)
USBDEVFS_FORBID_SUSPEND   = IO(ord("U"), 33)
USBDEVFS_ALLOW_SUSPEND    = IO(ord("U"), 34)
USBDEVFS_WAIT_FOR_RESUME  = IO(ord("U"), 35)

del IOC_READ, IOC_WRITE, IOC, IO, IOR, IOW, IOWR
