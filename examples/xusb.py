# Copyright (c) 2016 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/license/zlib

# xusb: Generic USB test program
# Copyright © 2009-2012 Pete Batard <pete@akeo.ie>
# Contributions to Mass Storage by Alan Stern.
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
import os
import re
import ctypes as ct

import libusb as usb
from libusb._platform import is_windows
if is_windows: import win32

usb_strerror   = lambda r: usb.strerror(r).decode("utf-8")
usb_error_name = lambda status: usb.error_name(status).decode("utf-8")

def msleep(msecs: int):
    if is_windows:
       win32.Sleep(msecs)
    else:
       ts = struct_timespec({ msecs / 1000, (msecs % 1000) * 1000000 })
       nanosleep(ct.byref(ts), NULL)

# Future versions of libusb will use usb_interface instead of interface
# in libusb.config_descriptor => catter for that
#define usb_interface interface

# Global variables
binary_dump          = False  # bool
binary_name          = None   # str|None
extra_info           = False  # bool
force_device_request = False  # bool # For WCID descriptor queries

def perr(fmt, *args):
    print(fmt.format(*args), file=sys.stderr, end="")
    sys.stderr.flush()

def err_exit(errcode):
    perr("   {}\n", usb.strerror(errcode).decode("utf-8"))
    return -1

B           = lambda x: 1 if x != 0 else 0
be_to_int32 = lambda buf: (buf[0] << 24) | (buf[1] << 16) | (buf[2] << 8) | buf[3]

RETRY_MAX            = 5
REQUEST_SENSE_LENGTH = 0x12
INQUIRY_LENGTH       = 0x24
READ_CAPACITY_LENGTH = 0x08

# HID Class-Specific Requests values.
# See section 7.2 of the HID specifications
HID_GET_REPORT          = 0x01
HID_GET_IDLE            = 0x02
HID_GET_PROTOCOL        = 0x03
HID_SET_REPORT          = 0x09
HID_SET_IDLE            = 0x0A
HID_SET_PROTOCOL        = 0x0B
HID_REPORT_TYPE_INPUT   = 0x01
HID_REPORT_TYPE_OUTPUT  = 0x02
HID_REPORT_TYPE_FEATURE = 0x03

# Mass Storage Requests values.
# See section 3 of the Bulk-Only Mass Storage Class specifications
BOMS_RESET       = 0xFF
BOMS_GET_MAX_LUN = 0xFE

# Microsoft OS Descriptor
MS_OS_DESC_STRING_INDEX       = 0xEE
MS_OS_DESC_STRING_LENGTH      = 0x12
MS_OS_DESC_VENDOR_CODE_OFFSET = 0x10
#static const
ms_os_desc_string = (ct.c_uint8 * 16)(
    MS_OS_DESC_STRING_LENGTH,
    usb.LIBUSB_DT_STRING,
    ord(b'M'), 0, ord(b'S'), 0, ord(b'F'), 0, ord(b'T'), 0,
    ord(b'1'), 0, ord(b'0'), 0, ord(b'0'), 0,
)

# Section 5.1: Command Block Wrapper (CBW)
class command_block_wrapper(ct.Structure):
    _fields_ = [
    ("dCBWSignature",          (ct.c_uint8 * 4)),
    ("dCBWTag",                ct.c_uint32),
    ("dCBWDataTransferLength", ct.c_uint32),
    ("bmCBWFlags",             ct.c_uint8),
    ("bCBWLUN",                ct.c_uint8),
    ("bCBWCBLength",           ct.c_uint8),
    ("CBWCB",                  (ct.c_uint8 * 16)),
]

# Section 5.2: Command Status Wrapper (CSW)
class command_status_wrapper(ct.Structure):
    _fields_ = [
    ("dCSWSignature",   (ct.c_uint8 * 4)),
    ("dCSWTag",         ct.c_uint32),
    ("dCSWDataResidue", ct.c_uint32),
    ("bCSWStatus",      ct.c_uint8),
]

#static const
cdb_length = (ct.c_uint8 * 256)(
   # 0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F
     6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6,  # 0
     6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6,  # 1
    10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,  # 2
    10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,  # 3
    10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,  # 4
    10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,  # 5
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # 6
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # 7
    16,16,16,16,16,16,16,16,16,16,16,16,16,16,16,16,  # 8
    16,16,16,16,16,16,16,16,16,16,16,16,16,16,16,16,  # 9
    12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,  # A
    12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,  # B
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # C
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # D
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # E
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,     # F
)
cdb_length[255] = 0

test_type = ct.c_int
(
    USE_GENERIC,
    USE_PS3,
    USE_XBOX,
    USE_SCSI,
    USE_HID
) = (0, 1, 2, 3, 4)

test_mode = USE_GENERIC

VID = 0  # ct.c_uint16
PID = 0  # ct.c_uint16


#static
#@annotate(buffer=unsigned char*, size=unsigned int)
def display_buffer_hex(buffer, size):

    for i in range(0, size, 16):
        print("\n  {:08x}  ".format(i), end="")
        for j in range(16):
            if i + j < size:
                print("{:02x}".format(buffer[i + j]), end="")
            else:
                print("  ", end="")
            print(" ", end="")
        print(" ", end="")
        for j in range(16):
            if i + j < size:
                if buffer[i + j] < 32 or buffer[i + j] > 126:
                    print(".", end="")
                else:
                    print("%c" % buffer[i + j], end="")
    print()


#static
#@annotate(str|None, uuid=const ct.POINTER(ct.c_uint8))
def uuid_to_string(uuid):

    if uuid == NULL:
        return None
    return ("{{{:02x}{:02x}{:02x}{:02x}-{:02x}{:02x}-{:02x}{:02x}"
            "-{:02x}{:02x}-{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}}}".format(
            uuid[0], uuid[1], uuid[2],  uuid[3],  uuid[4],  uuid[5],  uuid[6],  uuid[7],
            uuid[8], uuid[9], uuid[10], uuid[11], uuid[12], uuid[13], uuid[14], uuid[15]))


#static
#@annotate(handle=ct.POINTER(usb.device_handle))
def display_ps3_status(handle) -> int:

    # The PS3 Controller is really a HID device that got its HID Report Descriptors
    # removed by Sony

    input_report      = (ct.c_uint8 * 49)()
    master_bt_address = (ct.c_uint8 *  8)()
    device_bt_address = (ct.c_uint8 * 18)()

    # Get the controller's bluetooth address of its master device
    r = usb.control_transfer(handle,
                             usb.LIBUSB_ENDPOINT_IN |
                             usb.LIBUSB_REQUEST_TYPE_CLASS |
                             usb.LIBUSB_RECIPIENT_INTERFACE,
                             HID_GET_REPORT,
                             0x03f5, 0,
                             master_bt_address,
                             ct.sizeof(master_bt_address),
                             100)
    if r < 0:
        return err_exit(r)
    print("\nMaster's bluetooth address: "
          "{:02X}:{:02X}:{:02X}:{:02X}:{:02X}:{:02X}".format(
          master_bt_address[2], master_bt_address[3], master_bt_address[4],
          master_bt_address[5], master_bt_address[6], master_bt_address[7]))

    # Get the controller's bluetooth address
    r = usb.control_transfer(handle,
                             usb.LIBUSB_ENDPOINT_IN |
                             usb.LIBUSB_REQUEST_TYPE_CLASS |
                             usb.LIBUSB_RECIPIENT_INTERFACE,
                             HID_GET_REPORT,
                             0x03f2, 0,
                             device_bt_address,
                             ct.sizeof(device_bt_address),
                             100)
    if r < 0:
        return err_exit(r)
    print("\nMaster's bluetooth address: "
          "{:02X}:{:02X}:{:02X}:{:02X}:{:02X}:{:02X}".format(
          device_bt_address[4], device_bt_address[5], device_bt_address[6],
          device_bt_address[7], device_bt_address[8], device_bt_address[9]))

    # Get the status of the controller's buttons via its HID report
    print("\nReading PS3 Input Report...")
    r = usb.control_transfer(handle,
                             usb.LIBUSB_ENDPOINT_IN |
                             usb.LIBUSB_REQUEST_TYPE_CLASS |
                             usb.LIBUSB_RECIPIENT_INTERFACE,
                             HID_GET_REPORT,
                             (HID_REPORT_TYPE_INPUT << 8) | 0x01, 0,
                             input_report,
                             ct.sizeof(input_report),
                             1000)
    if r < 0:
        return err_exit(r)
    pressed = input_report[2]  # Direction pad plus start, select, and joystick buttons
    if   pressed == 0x01: print("\tSELECT pressed")
    elif pressed == 0x02: print("\tLEFT 3 pressed")
    elif pressed == 0x04: print("\tRIGHT 3 pressed")
    elif pressed == 0x08: print("\tSTART pressed")
    elif pressed == 0x10: print("\tUP pressed")
    elif pressed == 0x20: print("\tRIGHT pressed")
    elif pressed == 0x40: print("\tDOWN pressed")
    elif pressed == 0x80: print("\tLEFT pressed")
    pressed = input_report[3]  # Shapes plus top right and left buttons
    if   pressed == 0x01: print("\tLEFT 2 pressed")
    elif pressed == 0x02: print("\tRIGHT 2 pressed")
    elif pressed == 0x04: print("\tLEFT 1 pressed")
    elif pressed == 0x08: print("\tRIGHT 1 pressed")
    elif pressed == 0x10: print("\tTRIANGLE pressed")
    elif pressed == 0x20: print("\tCIRCLE pressed")
    elif pressed == 0x40: print("\tCROSS pressed")
    elif pressed == 0x80: print("\tSQUARE pressed")
    print("\tPS button: {:d}".format(input_report[4]))
    print("\tLeft Analog (X,Y): ({:d},{:d})".format(input_report[6],  input_report[7]))
    print("\tRight Analog (X,Y): ({:d},{:d})".format(input_report[8], input_report[9]))
    print("\tL2 Value: {:d}\tR2 Value: {:d}".format(input_report[18], input_report[19]))
    print("\tL1 Value: {:d}\tR1 Value: {:d}".format(input_report[20], input_report[21]))
    print("\tRoll (x axis): {:d} Yaw (y axis): {:d} Pitch (z axis) {:d}".format(
            #(((input_report[42] + 128) % 256) - 128),
            ct.c_int8(input_report[42]).value,
            ct.c_int8(input_report[44]).value,
            ct.c_int8(input_report[46]).value))
    print("\tAcceleration: {:d}".format(ct.c_int8(input_report[48]).value))
    print()

    return 0


#static
#@annotate(handle=ct.POINTER(usb.device_handle))
def display_xbox_status(handle) -> int:

    # The XBOX Controller is really a HID device that got its HID Report Descriptors
    # removed by Microsoft.
    # Input/Output reports described at http://euc.jp/periphs/xbox-controller.ja.html

    input_report = (20 * ct.c_uint8)()

    print("\nReading XBox Input Report...")
    r = usb.control_transfer(handle,
                             usb.LIBUSB_ENDPOINT_IN |
                             usb.LIBUSB_REQUEST_TYPE_CLASS |
                             usb.LIBUSB_RECIPIENT_INTERFACE,
                             HID_GET_REPORT,
                             (HID_REPORT_TYPE_INPUT << 8) | 0x00, 0,
                             input_report, 20,
                             1000)
    if r < 0:
        return err_exit(r)
    print("   D-pad: {:02X}".format(input_report[2] & 0x0F))
    print("   Start:{:d}, Back:{:d}, "
          "Left Stick Press:{:d}, Right Stick Press:{:d}".format(
          B(input_report[2] & 0x10), B(input_report[2] & 0x20),
          B(input_report[2] & 0x40), B(input_report[2] & 0x80)))
    # A, B, X, Y, Black, White are pressure sensitive
    print("   A:{:d}, B:{:d}, X:{:d}, Y:{:d}, White:{:d}, Black:{:d}".format(
          input_report[4], input_report[5], input_report[6],
          input_report[7], input_report[9], input_report[8]))
    print("   Left Trigger: {:d}, Right Trigger: {:d}".format(
          input_report[10], input_report[11]))
    print("   Left Analog (X,Y): ({:d},{:d})".format(
          int16_t((input_report[13] << 8) | input_report[12]),
          int16_t((input_report[15] << 8) | input_report[14])))
    print("   Right Analog (X,Y): ({:d},{:d})".format(
          int16_t((input_report[17] << 8) | input_report[16]),
          int16_t((input_report[19] << 8) | input_report[18])))
    return 0


#static
#@annotate(handle=ct.POINTER(usb.device_handle), left=ct.c_uint8, right=ct.c_uint8)
def set_xbox_actuators(handle, left, right) -> int:

    print("\nWriting XBox Controller Output Report...")

    output_report = (6 * ct.c_uint8)()
    output_report[1] = ct.sizeof(output_report)
    output_report[3] = left
    output_report[5] = right

    r = usb.control_transfer(handle,
                             usb.LIBUSB_ENDPOINT_OUT |
                             usb.LIBUSB_REQUEST_TYPE_CLASS |
                             usb.LIBUSB_RECIPIENT_INTERFACE,
                             HID_SET_REPORT,
                             (HID_REPORT_TYPE_OUTPUT << 8) | 0x00, 0,
                             output_report, 6,
                             1000)
    if r < 0:
        return err_exit(r)
    return 0


_tag = 1  # ct.c_uint32
#static
#@annotate(int, handle=ct.POINTER(usb.device_handle), endpoint=int)
#          ct.c_uint8 lun, ct.c_uint8* cdb, ct.c_uint8 direction, int data_length,
#          ct.c_uint32* ret_tag):
def send_mass_storage_command(handle, endpoint, lun, cdb, direction, data_length, ret_tag):

    global _tag

    #int i, r;

    cbw = command_block_wrapper()

    if not cdb:
        return -1

    if endpoint & usb.LIBUSB_ENDPOINT_IN:
        perr("send_mass_storage_command: cannot send command on IN endpoint\n")
        return -1

   #ct.c_uint8 cdb_len;
    cdb_len = cdb_length[cdb[0]]
    if cdb_len == 0 or cdb_len > ct.sizeof(cbw.CBWCB):
        perr("send_mass_storage_command: don't know how to handle this command ({:02X}, length {:d})\n",
             cdb[0], cdb_len)
        return -1

    cbw.dCBWSignature[0] = 'U'
    cbw.dCBWSignature[1] = 'S'
    cbw.dCBWSignature[2] = 'B'
    cbw.dCBWSignature[3] = 'C'
    ret_tag[0] = _tag
    cbw.dCBWTag                = _tag
    cbw.dCBWDataTransferLength = data_length
    cbw.bmCBWFlags             = direction
    cbw.bCBWLUN                = lun
    _tag += 1
    # Subclass is 1 or 6 => cdb_len
    cbw.bCBWCBLength = cdb_len
    memcpy(cbw.CBWCB, cdb, cdb_len);

    i = 0
    while True:
        # The transfer length must always be exactly 31 bytes.
        size = ct.c_int()
        r = usb.bulk_transfer(handle, endpoint, ct.cast(ct.pointer(cbw), ct.POINTER(ct.c_ubyte)), 31, ct.byref(size), 1000)
        if r == usb.LIBUSB_ERROR_PIPE:
            usb.clear_halt(handle, endpoint)
        i += 1
        if r != usb.LIBUSB_ERROR_PIPE or i >= RETRY_MAX:
            break
    if r != usb.LIBUSB_SUCCESS:
        perr("   send_mass_storage_command: {}\n", usb_strerror(r))
        return -1

    print("   sent {:d} CDB bytes".format(cdb_len))
    return 0


#static
#@annotate(handle=ct.POINTER(usb.device_handle), endpoint=int, ct.c_uint32 expected_tag)
def get_mass_storage_status(handle, endpoint, expected_tag) -> int:

    #int r;

    csw = command_status_wrapper()

    # The device is allowed to STALL this transfer. If it does, you have to
    # clear the stall and try again.
    i = 0;
    while True:
        size = ct.c_int()
        r = usb.bulk_transfer(handle, endpoint, ct.cast(ct.pointer(csw), ct.POINTER(ct.c_ubyte)), 13, ct.byref(size), 1000)
        if r == usb.LIBUSB_ERROR_PIPE:
            usb.clear_halt(handle, endpoint)
        i += 1
        if r != usb.LIBUSB_ERROR_PIPE or i >= RETRY_MAX:
            break
    if r != usb.LIBUSB_SUCCESS:
        perr("   get_mass_storage_status: {}\n", usb_strerror(r))
        return -1
    size = size.value
    if size != 13:
        perr("   get_mass_storage_status: received {:d} bytes (expected 13)\n", size)
        return -1
    if csw.dCSWTag != expected_tag:
        perr("   get_mass_storage_status: mismatched tags (expected {:08X}, received {:08X})\n",
             expected_tag, csw.dCSWTag)
        return -1
    # For this test, we ignore the dCSWSignature check for validity...
    print("   Mass Storage Status: {:02X} ({})".format(
          csw.bCSWStatus, "FAILED" if csw.bCSWStatus else "Success"))
    if csw.dCSWTag != expected_tag:
        return -1
    if csw.bCSWStatus:
        # REQUEST SENSE is appropriate only if bCSWStatus is 1, meaning that the
        # command failed somehow.  Larger values (2 in particular) mean that
        # the command couldn't be understood.
        if csw.bCSWStatus == 1:
            return -2  # request Get Sense
        else:
            return -1

    # In theory we also should check dCSWDataResidue.  But lots of devices
    # set it wrongly.
    return 0


#static
#@annotate(handle=ct.POINTER(usb.device_handle), endpoint_in=int, endpoint_out=int)
def get_sense(handle, endpoint_in, endpoint_out):

    # Request Sense
    print("Request Sense:")
    sense = (ct.c_uint8 * 18)()
    cdb   = (ct.c_uint8 * 16)()  # SCSI Command Descriptor Block
    cdb[0] = 0x03  # Request Sense
    cdb[4] = REQUEST_SENSE_LENGTH

    expected_tag = ct.c_uint32()
    send_mass_storage_command(handle, endpoint_out, 0, cdb, usb.LIBUSB_ENDPOINT_IN, REQUEST_SENSE_LENGTH, ct.pointer(expected_tag))
    size = ct.c_int()
    rc = usb.bulk_transfer(handle, endpoint_in, ct.cast(ct.pointer(sense), ct.POINTER(ct.c_ubyte)), REQUEST_SENSE_LENGTH, ct.byref(size), 1000)
    if rc < 0:
        print("libusb.bulk_transfer failed: {}".format(usb_error_name(rc)))
        return

    size = size.value
    print("   received {:d} bytes".format(size))

    if sense[0] != 0x70 and sense[0] != 0x71:
        perr("   ERROR No sense data\n")
    else:
        perr("   ERROR Sense: {:02X} {:02X} {:02X}\n",
             sense[2] & 0x0F, sense[12], sense[13])

    # Strictly speaking, the get_mass_storage_status() call should come
    # before these perr() lines.  If the status is nonzero then we must
    # assume there's no data in the buffer.  For xusb it doesn't matter.
    get_mass_storage_status(handle, endpoint_in, expected_tag)


#static
#@annotate(handle=ct.POINTER(usb.device_handle), endpoint_in=int, endpoint_out=int)
def test_mass_storage(handle, endpoint_in, endpoint_out) -> int:

    # Mass Storage device to test bulk transfers (non destructive test)

    global binary_dump
    global binary_name

    #int r;
    #ct.c_uint32 i

    print("\nReading Max LUN:")
    lun = ct.c_uint8()
    r = usb.control_transfer(handle,
                             usb.LIBUSB_ENDPOINT_IN |
                             usb.LIBUSB_REQUEST_TYPE_CLASS |
                             usb.LIBUSB_RECIPIENT_INTERFACE,
                             BOMS_GET_MAX_LUN,
                             0, 0,
                             ct.byref(lun), 1,
                             1000)
    lun = lun.value
    # Some devices send a STALL instead of the actual value.
    # In such cases we should set lun to 0.
    if r == usb.LIBUSB_ERROR_PIPE:
        lun = 0
        print("   Stalled, setting Max LUN to 0")
    elif r < 0:
        perr("   Failed.\n")
        return r
    else:
        print("   Max LUN = {:d}".format(lun))

    # Send Inquiry
    print("\nSending Inquiry:")
    buffer = (ct.c_uint8 * 64)()
    cdb    = (ct.c_uint8 * 16)()  # SCSI Command Descriptor Block
    cdb[0] = 0x12  # Inquiry
    cdb[4] = INQUIRY_LENGTH

    expected_tag = ct.c_uint32()
    send_mass_storage_command(handle, endpoint_out, lun, cdb, usb.LIBUSB_ENDPOINT_IN, INQUIRY_LENGTH, ct.pointer(expected_tag))
    size = ct.c_int()
    r = usb.bulk_transfer(handle, endpoint_in, ct.cast(ct.pointer(buffer), ct.POINTER(ct.c_ubyte)), INQUIRY_LENGTH, ct.byref(size), 1000)
    if r < 0:
        return err_exit(r)
    size = size.value
    print("   received {:d} bytes".format(size))
    # The following strings are not zero terminated
    vid = (ct.c_char * 9)()
    pid = (ct.c_char * 9)()
    rev = (ct.c_char * 5)()
    for i in range(8):
        vid[i]     = buffer[8  + i]
        pid[i]     = buffer[16 + i]
        rev[i / 2] = buffer[32 + i / 2]  # instead of another loop
    vid[8] = 0
    pid[8] = 0
    rev[4] = 0
    print("   VID:PID:REV \"{:>8s}\":\"{:>8s}\":\"{:>4s}\"".format(vid, pid, rev))
    if get_mass_storage_status(handle, endpoint_in, expected_tag) == -2:
        get_sense(handle, endpoint_in, endpoint_out)

    # Read capacity
    print("\nReading Capacity:")
    buffer = (ct.c_uint8 * 64)()
    cdb    = (ct.c_uint8 * 16)()  # SCSI Command Descriptor Block
    cdb[0] = 0x25  # Read Capacity

    expected_tag = ct.c_uint32()
    send_mass_storage_command(handle, endpoint_out, lun, cdb, usb.LIBUSB_ENDPOINT_IN, READ_CAPACITY_LENGTH, ct.pointer(expected_tag))
    size = ct.c_int()
    r = usb.bulk_transfer(handle, endpoint_in, ct.cast(ct.pointer(buffer), ct.POINTER(ct.c_ubyte)), READ_CAPACITY_LENGTH, ct.byref(size), 1000)
    if r < 0:
        return err_exit(r)
    size = size.value
    print("   received {:d} bytes".format(size))
    max_lba     = be_to_int32(buffer[0:])
    block_size  = be_to_int32(buffer[4:])
    device_size = (max_lba + 1.0) * block_size / (1024 * 1024 * 1024)
    print("   Max LBA: {:08X}, Block Size: {:08X} ({:.2f} GB)".format(
          max_lba, block_size, device_size))
    if get_mass_storage_status(handle, endpoint_in, expected_tag) == -2:
        get_sense(handle, endpoint_in, endpoint_out)

    # coverity[tainted_data]
    try:
        data = (ct.c_ubyte * block_size)()
        ct.memset(data, b"\0", block_size * ct.sizeof(ct.c_ubyte))
    except:
        perr("   unable to allocate data buffer\n")
        return -1

    # Send Read
    print("\nAttempting to read {:d} bytes:".format(block_size))
    cdb    = (ct.c_uint8 * 16)()  # SCSI Command Descriptor Block
    cdb[0] = 0x28  # Read(10)
    cdb[8] = 0x01  # 1 block

    expected_tag = ct.c_uint32()
    send_mass_storage_command(handle, endpoint_out, lun, cdb, usb.LIBUSB_ENDPOINT_IN, block_size, ct.pointer(expected_tag))
    size = ct.c_int()
    usb.bulk_transfer(handle, endpoint_in, data, block_size, ct.byref(size), 5000)
    size = size.value
    print("   READ: received {:d} bytes".format(size))
    if get_mass_storage_status(handle, endpoint_in, expected_tag) == -2:
        get_sense(handle, endpoint_in, endpoint_out)
    else:
        display_buffer_hex(data, size)
        if binary_dump:
            try:
                fd = open(binary_name, "w")
            except: pass
            else:
                with fd:
                    if fd.fwrite(data, ct.c_size_t(size).value) != ct.c_uint(size).value:
                        perr("   unable to write binary data\n")

    del data

    return 0


# HID

#static
#@annotate(int, ct.c_uint8* hid_report_descriptor, int size, int type)
def get_hid_record_size(hid_report_descriptor, size, type):

    record_size = [0, 0, 0]  # [int, ...]
    nb_bits  = 0  # int
    nb_items = 0  # int

    found_record_marker = False
    j = 0
    i = hid_report_descriptor[0] + 1
    while i < size:
        offset = (hid_report_descriptor[i] & 0x03) + 1  # ct.c_uint8
        if offset == 4:
            offset = 5
        kind_of = hid_report_descriptor[i] & 0xFC
        if kind_of == 0x74:  # bitsize
            nb_bits = hid_report_descriptor[i + 1]
        elif kind_of == 0x94:  # count
            nb_items = 0
            for j in range(1, offset):
                nb_items = ct.c_uint32(hid_report_descriptor[i + j]).value << (8 * (j - 1))
            i = offset  # ???
        elif kind_of == 0x80:  # input
            found_record_marker = True
            j = 0
        elif kind_of == 0x90:  # output
            found_record_marker = True
            j = 1
        elif kind_of == 0xb0:  # feature
            found_record_marker = True
            j = 2
        elif kind_of == 0xC0:  # end of collection
            nb_items = 0
            nb_bits  = 0
        else:
            i += offset
            continue
        if found_record_marker:
            found_record_marker = False
            record_size[j] += nb_items * nb_bits
        i += offset

    if type < HID_REPORT_TYPE_INPUT or type > HID_REPORT_TYPE_FEATURE:
        return 0
    else:
        return (record_size[type - HID_REPORT_TYPE_INPUT] + 7) / 8


#static
#@annotate(handle=ct.POINTER(usb.device_handle), endpoint_in=int)
def test_hid(handle, endpoint_in) -> int:

    global binary_dump
    global binary_name

    #int r;

    hid_report_descriptor = (ct.c_uint8 * 256)()
    report_buffer = ct.POINTER(ct.c_uint8)()

    print("\nReading HID Report Descriptors:")
    descriptor_size = usb.control_transfer(handle,
                                           usb.LIBUSB_ENDPOINT_IN |
                                           usb.LIBUSB_REQUEST_TYPE_STANDARD |
                                           usb.LIBUSB_RECIPIENT_INTERFACE,
                                           usb.LIBUSB_REQUEST_GET_DESCRIPTOR,
                                           usb.LIBUSB_DT_REPORT << 8, 0,
                                           hid_report_descriptor,
                                           ct.sizeof(hid_report_descriptor),
                                           1000)
    if descriptor_size < 0:
        print("   Failed")
        return -1
    display_buffer_hex(hid_report_descriptor, descriptor_size)
    if binary_dump:
        try:
            fd = open(binary_name, "w")
        except: pass
        else:
            with fd:
                if fd.fwrite(hid_report_descriptor, descriptor_size) != descriptor_size:
                    print("   Error writing descriptor to file")

    size = get_hid_record_size(hid_report_descriptor, descriptor_size, HID_REPORT_TYPE_FEATURE)
    if size <= 0:
        print("\nSkipping Feature Report readout (None detected)")
    else:
        try:
            report_buffer = (ct.c_uint8 * size)()
            ct.memset(report_buffer, b"\0", size * ct.sizeof(ct.c_uint8))
        except:
            return -1

        print("\nReading Feature Report (length {:d})...".format(size))
        r = usb.control_transfer(handle,
                                 usb.LIBUSB_ENDPOINT_IN |
                                 usb.LIBUSB_REQUEST_TYPE_CLASS |
                                 usb.LIBUSB_RECIPIENT_INTERFACE,
                                 HID_GET_REPORT,
                                 (HID_REPORT_TYPE_FEATURE << 8) | 0, 0,
                                 report_buffer, ct.c_uint16(size),
                                 5000)
        if r >= 0:
            display_buffer_hex(report_buffer, size)
        else:
            if r == usb.LIBUSB_ERROR_NOT_FOUND:
                print("   No Feature Report available for this device")
            elif r == usb.LIBUSB_ERROR_PIPE:
                print("   Detected stall - resetting pipe...")
                usb.clear_halt(handle, 0)
            else:
                print("   Error: {}".format(usb_strerror(r)))

        del report_buffer

    size = get_hid_record_size(hid_report_descriptor, descriptor_size, HID_REPORT_TYPE_INPUT)
    if size <= 0:
        print("\nSkipping Input Report readout (None detected)")
    else:
        try:
            report_buffer = (ct.c_uint8 * size)()
            ct.memset(report_buffer, b"\0", size * ct.sizeof(ct.c_uint8))
        except:
            return -1

        print("\nReading Input Report (length {:d})...".format(size))
        r = usb.control_transfer(handle,
                                 usb.LIBUSB_ENDPOINT_IN |
                                 usb.LIBUSB_REQUEST_TYPE_CLASS |
                                 usb.LIBUSB_RECIPIENT_INTERFACE,
                                 HID_GET_REPORT,
                                 (HID_REPORT_TYPE_INPUT << 8) | 0x00, 0,
                                 report_buffer, ct.c_uint16(size),
                                 5000)
        if r >= 0:
            display_buffer_hex(report_buffer, size)
        else:
            if r == usb.LIBUSB_ERROR_TIMEOUT:
                print("   Timeout! Please make sure you act on the device within the 5 seconds allocated...")
            elif r == usb.LIBUSB_ERROR_PIPE:
                print("   Detected stall - resetting pipe...")
                usb.clear_halt(handle, 0)
            else:
                print("   Error: {}".format(usb_strerror(r)))

        # Attempt a bulk read from endpoint 0 (this should just return a raw input report)
        print("\nTesting interrupt read using endpoint {:02X}...".format(endpoint_in))
        r = usb.interrupt_transfer(handle, endpoint_in, report_buffer, size, ct.byref(size), 5000)
        if r >= 0:
            display_buffer_hex(report_buffer, size)
        else:
            print("   {}".format(usb_strerror(r)))

        del report_buffer

    return 0


#static
#@annotate(handle=ct.POINTER(usb.device_handle), ct.c_uint8 bRequest, int iface_number)
def read_ms_winsub_feature_descriptors(handle, bRequest, iface_number):

    # Read the MS WinUSB Feature Descriptors, that are used on Windows 8 for automated driver installation

    MAX_OS_FD_LENGTH = 256

    #int r;

    os_desc = (ct.c_uint8 * MAX_OS_FD_LENGTH)()

    class struct_os_fd(ct.Structure):
        _fields_ = [
        ("desc",        ct.c_char_p),
        ("recipient",   ct.c_uint8),
        ("index",       ct.c_uint16),
        ("header_size", ct.c_uint16),
    ]
    os_fd = [
        struct_os_fd(b"Extended Compat ID",  usb.LIBUSB_RECIPIENT_DEVICE,    0x0004, 0x10),
        struct_os_fd(b"Extended Properties", usb.LIBUSB_RECIPIENT_INTERFACE, 0x0005, 0x0A),
    ]

    if iface_number < 0:
        return

    # WinUSB has a limitation that forces wIndex to the interface number when issuing
    # an Interface Request. To work around that, we can force a Device Request for
    # the Extended Properties, assuming the device answers both equally.
    if force_device_request:
        os_fd[1].recipient = usb.LIBUSB_RECIPIENT_DEVICE

    for i in range(2):

        print("\nReading {} OS Feature Descriptor (wIndex = 0x{:04x}):".format(
              os_fd[i].desc.decode("utf-8"), os_fd[i].index))

        # Read the header part
        r = usb.control_transfer(handle,
                                 ct.c_uint8(usb.LIBUSB_ENDPOINT_IN |
                                            usb.LIBUSB_REQUEST_TYPE_VENDOR |
                                            os_fd[i].recipient),
                                 bRequest,
                                 ct.c_uint16((iface_number << 8) | 0x00), os_fd[i].index,
                                 os_desc, os_fd[i].header_size,
                                 1000)
        if r < os_fd[i].header_size:
            perr("   Failed: {}", usb_strerror(r)
                                  if r < 0 else "header size is too small")
            return
        le_type_punning_IS_fine = ct.cast(os_desc, ct.c_void_p)
        length = ct.cast(le_type_punning_IS_fine, ct.POINTER(ct.c_uint32))[0].value  # ct.c_uint32
        length = min(length, MAX_OS_FD_LENGTH)

        # Read the full feature descriptor
        r = usb.control_transfer(handle,
                                 ct.c_uint8(usb.LIBUSB_ENDPOINT_IN |
                                            usb.LIBUSB_REQUEST_TYPE_VENDOR |
                                            os_fd[i].recipient),
                                 bRequest,
                                 ct.c_uint16((iface_number << 8) | 0x00), os_fd[i].index,
                                 os_desc, ct.c_uint16(length),
                                 1000)
        if r < 0:
            perr("   Failed: {}", usb_strerror(r))
            return
        else:
            display_buffer_hex(os_desc, r)


#@annotate(dev_cap=ct.POINTER(usb.bos_dev_capability_descriptor))
def print_device_cap(dev_cap):

    if dev_cap[0].bDevCapabilityType == usb.LIBUSB_BT_USB_2_0_EXTENSION:

        usb_2_0_ext = ct.POINTER(usb.usb_2_0_extension_descriptor)()
        usb.get_usb_2_0_extension_descriptor(None, dev_cap, ct.byref(usb_2_0_ext))
        if usb_2_0_ext:
            print("    USB 2.0 extension:")
            print("      attributes             : {:02X}".format(usb_2_0_ext[0].bmAttributes))
            usb.free_usb_2_0_extension_descriptor(usb_2_0_ext)

    elif dev_cap[0].bDevCapabilityType == usb.LIBUSB_BT_SS_USB_DEVICE_CAPABILITY:

        ss_usb_device_cap = ct.POINTER(usb.ss_usb_device_capability_descriptor)()
        usb.get_ss_usb_device_capability_descriptor(None, dev_cap, ct.byref(ss_usb_device_cap))
        if ss_usb_device_cap:
            print("    USB 3.0 capabilities:")
            print("      attributes             : {:02X}".format(ss_usb_device_cap[0].bmAttributes))
            print("      supported speeds       : {:04X}".format(ss_usb_device_cap[0].wSpeedSupported))
            print("      supported functionality: {:02X}".format(ss_usb_device_cap[0].bFunctionalitySupport))
            usb.free_ss_usb_device_capability_descriptor(ss_usb_device_cap)

    elif dev_cap[0].bDevCapabilityType == usb.LIBUSB_BT_CONTAINER_ID:

        container_id = ct.POINTER(usb.container_id_descriptor)()
        usb.get_container_id_descriptor(None, dev_cap, ct.byref(container_id))
        if container_id:
            print("    Container ID:\n      {}".format(uuid_to_string(container_id[0].ContainerID)))
            usb.free_container_id_descriptor(container_id)

    elif dev_cap[0].bDevCapabilityType == usb.LIBUSB_BT_PLATFORM_DESCRIPTOR:

        platform_descriptor = ct.POINTER(usb.platform_descriptor)()
        usb.get_platform_descriptor(None, dev_cap, ct.byref(platform_descriptor))
        if platform_descriptor:
            print("    Platform descriptor:")
            print("      bLength                : {:d}".format(platform_descriptor[0].bLength))
            print("      PlatformCapabilityUUID : {}".format(uuid_to_string(platform_descriptor[0].PlatformCapabilityUUID)))
            display_buffer_hex(platform_descriptor[0].CapabilityData, platform_descriptor[0].bLength - 20)
            print()
            usb.free_platform_descriptor(platform_descriptor)
    else:
        print("    Unknown BOS device capability {:02x}:".format(dev_cap[0].bDevCapabilityType))


#static
#@annotate(ct.c_uint16 vid, ct.c_uint16 pid)
def test_device(vid, pid) -> int:

    global test_mode

    #int r;

    speed_name = [
        "Unknown",
        "1.5 Mbit/s (USB LowSpeed)",
        "12 Mbit/s (USB FullSpeed)",
        "480 Mbit/s (USB HighSpeed)",
        "5000 Mbit/s (USB SuperSpeed)",
        "10000 Mbit/s (USB SuperSpeedPlus)",
    ]

    print("Opening device {:04X}:{:04X}...".format(vid, pid))
   #handle = ct.POINTER(usb.device_handle)()
    handle = usb.open_device_with_vid_pid(None, vid, pid)
    if not handle:
        perr("  Failed.\n")
        return -1

    endpoint_in  = 0  # default IN  endpoint
    endpoint_out = 0  # default OUT endpoint

    try:
        dev = usb.get_device(handle)   # usb.device*
        bus = usb.get_bus_number(dev)  # ct.c_uint8
        if extra_info:
            port_path = (ct.c_uint8 * 8)()
            r = usb.get_port_numbers(dev, port_path, ct.sizeof(port_path))
            if r > 0:
                print("\nDevice properties:")
                print("        bus number: {}".format(bus))
                print("         port path: {}".format(port_path[0]), end="")
                for i in range(1, r):
                    print("->{}".format(port_path[i]), end="")
                print(" (from root hub)")
            r = usb.get_device_speed(dev)
            if r < 0 or r > 5: r = 0
            print("             speed: {}".format(speed_name[r]))

        print("\nReading device descriptor:")
        dev_desc = usb.device_descriptor()
        r = usb.get_device_descriptor(dev, ct.byref(dev_desc))
        if r < 0:
            return err_exit(r)
        print("            length: {}".format(dev_desc.bLength))
        print("      device class: {}".format(dev_desc.bDeviceClass))
        print("               S/N: {}".format(dev_desc.iSerialNumber))
        print("           VID:PID: {:04X}:{:04X}".format(dev_desc.idVendor,
                                                         dev_desc.idProduct))
        print("         bcdDevice: {:04X}".format(dev_desc.bcdDevice))
        print("   iMan:iProd:iSer: {}:{}:{}".format(
              dev_desc.iManufacturer, dev_desc.iProduct, dev_desc.iSerialNumber))
        print("          nb confs: {}".format(dev_desc.bNumConfigurations))
        # Copy the string descriptors for easier parsing
        string_index = (ct.c_uint8 * 3)()  # indexes of the string descriptors
        string_index[0] = dev_desc.iManufacturer
        string_index[1] = dev_desc.iProduct
        string_index[2] = dev_desc.iSerialNumber

        print("\nReading BOS descriptor: ", end="")
        bos_desc = ct.POINTER(usb.bos_descriptor)()
        if usb.get_bos_descriptor(handle, ct.byref(bos_desc)) == usb.LIBUSB_SUCCESS:
            print("{} caps".format(bos_desc[0].bNumDeviceCaps))
            for i in range(bos_desc[0].bNumDeviceCaps):
                print_device_cap(bos_desc[0].dev_capability[i])
            usb.free_bos_descriptor(bos_desc)
        else:
            print("no descriptor")

        print("\nReading first configuration descriptor:")
        conf_desc = ct.POINTER(usb.config_descriptor)()
        r = usb.get_config_descriptor(dev, 0, ct.byref(conf_desc))
        if r < 0:
            return err_exit(r)
        print("              total length: {}".format(conf_desc[0].wTotalLength))
        print("         descriptor length: {}".format(conf_desc[0].bLength))
        nb_ifaces = conf_desc[0].bNumInterfaces  # int
        print("             nb interfaces: {}".format(nb_ifaces))
        first_iface = (conf_desc[0].interface[0].altsetting[0].bInterfaceNumber
                       if nb_ifaces > 0 else -1)
        for i in range(nb_ifaces):
            usb_interface = conf_desc[0].interface[i]
            print("              interface[{}]: id = {}".format(
                  i, usb_interface.altsetting[0].bInterfaceNumber))
            for j in range(usb_interface.num_altsetting):
                altsetting = usb_interface.altsetting[j]
                print("interface[{}].altsetting[{}]: num endpoints = {}".format(
                      i, j, altsetting.bNumEndpoints))
                print("   Class.SubClass.Protocol: {:02X}.{:02X}.{:02X}".format(
                      altsetting.bInterfaceClass,
                      altsetting.bInterfaceSubClass,
                      altsetting.bInterfaceProtocol))
                if (altsetting.bInterfaceClass == usb.LIBUSB_CLASS_MASS_STORAGE and
                    (altsetting.bInterfaceSubClass == 0x01 or
                     altsetting.bInterfaceSubClass == 0x06) and
                    altsetting.bInterfaceProtocol == 0x50):
                    # Mass storage devices that can use basic SCSI commands
                    test_mode = USE_SCSI
                for k in range(altsetting.bNumEndpoints):
                    endpoint = altsetting.endpoint[k]  # const usb.endpoint_descriptor*
                    print("       endpoint[{}].address: {:02X}".format(
                          k, endpoint.bEndpointAddress))
                    # Use the first interrupt or bulk IN/OUT endpoints as default for testing
                    if ((endpoint.bmAttributes & usb.LIBUSB_TRANSFER_TYPE_MASK) &
                        (usb.LIBUSB_TRANSFER_TYPE_BULK | usb.LIBUSB_TRANSFER_TYPE_INTERRUPT)):
                        if endpoint.bEndpointAddress & usb.LIBUSB_ENDPOINT_IN:
                            if not endpoint_in:
                                endpoint_in = endpoint.bEndpointAddress
                        else:
                            if not endpoint_out:
                                endpoint_out = endpoint.bEndpointAddress
                    print("           max packet size: {:04X}".format(endpoint.wMaxPacketSize))
                    print("          polling interval: {:02X}".format(endpoint.bInterval))
                    ep_comp = ct.POINTER(usb.ss_endpoint_companion_descriptor)()
                    usb.get_ss_endpoint_companion_descriptor(None, ct.byref(altsetting.endpoint[k]),
                                                             ct.byref(ep_comp))
                    if ep_comp:
                        print("                 max burst: {:02X}   (USB 3.0)".format(ep_comp[0].bMaxBurst))
                        print("        bytes per interval: {:04X} (USB 3.0)".format(ep_comp[0].wBytesPerInterval))
                        usb.free_ss_endpoint_companion_descriptor(ep_comp)

        usb.free_config_descriptor(conf_desc)

        usb.set_auto_detach_kernel_driver(handle, 1)
        for iface in range(nb_ifaces):
            print("\nKernel driver attached for interface {}: ".format(iface), end="")
            ret = usb.kernel_driver_active(handle, iface)
            if ret == 0:
                print("none")
            elif ret == 1:
                print("yes")
            elif ret == usb.LIBUSB_ERROR_NOT_SUPPORTED:
                print("(not supported)")
            else:
                perr("\n   Failed (error {}) {}\n", ret, usb_strerror(ret))

            print("\nClaiming interface {}...".format(iface))
            r = usb.claim_interface(handle, iface)
            if r != usb.LIBUSB_SUCCESS:
                perr("   Failed (error {}) {}\n", ret, usb_strerror(ret))

        print("\nReading string descriptors:")
        string = (ct.c_char * 128)()
        for i in range(3):
            if string_index[i] == 0:
                continue
            if usb.get_string_descriptor_ascii(handle, string_index[i],
                    ct.cast(string, ct.POINTER(ct.c_ubyte)), ct.sizeof(string)) > 0:
                print("   String ({:#04x}): \"{}\"".format(
                      string_index[i], string[:].rstrip(b"\0").decode("utf-8")))

        print("\nReading OS string descriptor:", end="")
        r = usb.get_string_descriptor(handle, MS_OS_DESC_STRING_INDEX, 0,
                                      ct.cast(string, ct.POINTER(ct.c_ubyte)), MS_OS_DESC_STRING_LENGTH)
        if (r == MS_OS_DESC_STRING_LENGTH and ms_os_desc_string[:ct.sizeof(ms_os_desc_string)]
                     == ct.cast(string, ct.POINTER(ct.c_uint8))[:ct.sizeof(ms_os_desc_string)]):
            # If this is a Microsoft OS String Descriptor,
            # attempt to read the WinUSB extended Feature Descriptors
            print()
            read_ms_winsub_feature_descriptors(handle,
                                               ct.c_uint8(ord(string[MS_OS_DESC_VENDOR_CODE_OFFSET])),
                                               first_iface)
        else:
            print(" no descriptor")

        if hasattr(usb, "get_interface_association_descriptors"):
            # Read IADs
            print("\nReading interface association descriptors (IADs) for first configuration:")
            iad_array = ct.POINTER(usb.interface_association_descriptor_array)()
            r = usb.get_interface_association_descriptors(dev, 0, ct.byref(iad_array))
            if r == usb.LIBUSB_SUCCESS:
                print("    nb IADs: {}".format(iad_array[0].length))
                for i in range(iad_array[0].length):
                    iad: usb.interface_association_descriptor = iad_array[0].iad[i]
                    print("      IAD {}:".format(i))
                    print("            bFirstInterface: {}".format(iad.bFirstInterface))
                    print("            bInterfaceCount: {}".format(iad.bInterfaceCount))
                    print("             bFunctionClass: {:02X}".format(iad.bFunctionClass))
                    print("          bFunctionSubClass: {:02X}".format(iad.bFunctionSubClass))
                    print("          bFunctionProtocol: {:02X}".format(iad.bFunctionProtocol))
                    if iad.iFunction:
                        if usb.get_string_descriptor_ascii(handle, iad.iFunction,
                                ct.cast(string, ct.POINTER(ct.c_ubyte)), ct.sizeof(string)) > 0:
                            print("                  iFunction: {} ({})".format(iad.iFunction, string))
                        else:
                            print("                  iFunction: {} "
                                  "(libusb.get_string_descriptor_ascii failed!)".format(iad.iFunction))
                    else:
                        print("                  iFunction: 0")
                usb.free_interface_association_descriptors(iad_array)

        if test_mode == USE_PS3:
            r = display_ps3_status(handle)
            if r < 0:
                return err_exit(r)
        elif test_mode == USE_XBOX:
            r = display_xbox_status(handle)
            if r < 0:
                return err_exit(r)
            r = set_xbox_actuators(handle, 128, 222)
            if r < 0:
                return err_exit(r)
            msleep(2000)
            r = set_xbox_actuators(handle, 0, 0)
            if r < 0:
                return err_exit(r)
        elif test_mode == USE_HID:
            test_hid(handle, endpoint_in)
        elif test_mode == USE_SCSI:
            r = test_mass_storage(handle, endpoint_in, endpoint_out)
            if r < 0:
                return err_exit(r)
        elif test_mode == USE_GENERIC:
            pass

        print()
        for iface in range(nb_ifaces):
            print("Releasing interface {}...".format(iface))
            usb.release_interface(handle, iface)

        print("Closing device...")
    finally:
        usb.close(handle)

    return 0


def main(argv=sys.argv):

    global VID, PID
    global test_mode
    global binary_dump
    global binary_name

    show_help  = False  # bool
    debug_mode = False  # bool
    error_lang = None   # char*

    # Default to generic, expecting VID:PID
    VID = 0
    PID = 0

    test_mode = USE_GENERIC

    endian_test = ct.c_uint16(0xBE00)
    if ct.cast(ct.pointer(endian_test), ct.POINTER(ct.c_uint8))[0] == 0xBE:
        print("Despite their natural superiority for end users, big endian\n"
              "CPUs are not supported with this program, sorry.")
        return 0

   #if len(argv) >= 2:
    for j in range(1, len(argv)):
        arglen = len(argv[j])
        if argv[j][0] in ('-', '/') and arglen >= 2:
            opt = argv[j][1]
            if opt == 'd':
                debug_mode = True
            elif opt == 'i':
                extra_info = True
            elif opt == 'w':
                force_device_request = True
            elif opt == 'b':
                j += 1
                if j >= len(argv) or argv[j][0] in ('-', '/'):
                    print("   Option -b requires a file name")
                    return 1
                binary_name = argv[j]
                binary_dump = True
            elif opt == 'l':
                j += 1
                if j >= len(argv) or argv[j][0] in ('-', '/'):
                    print("   Option -l requires an ISO 639-1 language parameter")
                    return 1
                error_lang = argv[j]
            elif opt == 'j':
                # OLIMEX ARM-USB-TINY JTAG, 2 channel composite device - 2 interfaces
                if not VID and not PID:
                    VID = 0x15BA
                    PID = 0x0004
            elif opt == 'k':
                # Generic 2 GB USB Key (SCSI Transparent/Bulk Only) - 1 interface
                if not VID and not PID:
                    VID = 0x0204
                    PID = 0x6025
            # The following tests will force VID:PID if already provided
            elif opt == 'p':
                # Sony PS3 Controller - 1 interface
                VID = 0x054C
                PID = 0x0268
                test_mode = USE_PS3
            elif opt == 's':
                # Microsoft Sidewinder Precision Pro Joystick - 1 HID interface
                VID = 0x045E
                PID = 0x0008
                test_mode = USE_HID
            elif opt == 'x':
                # Microsoft XBox Controller Type S - 1 interface
                VID = 0x045E
                PID = 0x0289
                test_mode = USE_XBOX
            else:
                show_help = True
        else:
            for i in range(arglen):
                if argv[j][i] == ':':
                    match = re.match(r"([-+]?(0[xX])?[\dA-Fa-f]+):([-+]?(0[xX])?[\dA-Fa-f]+)", argv[j])
                    if not match:
                        print("   Please specify VID & PID as \"vid:pid\" in hexadecimal format")
                        return 1
                    tmp_vid, tmp_pid = int(match.group(1), base=16), int(match.group(3), base=16)
                    VID = ct.c_uint16(tmp_vid).value
                    PID = ct.c_uint16(tmp_pid).value
                    break
            else:
                show_help = True

    if show_help or len(argv) == 1 or len(argv) > 7:
        print("usage: {} [-h] [-d] [-i] [-k] [-b file] [-l lang] [-j] [-x] [-s] [-p] [-w] [vid:pid]".format(argv[0]))
        print("   -h      : display usage")
        print("   -d      : enable debug output")
        print("   -i      : print topology and speed info")
        print("   -j      : test composite FTDI based JTAG device")
        print("   -k      : test Mass Storage device")
        print("   -b file : dump Mass Storage data to file 'file'")
        print("   -p      : test Sony PS3 SixAxis controller")
        print("   -s      : test Microsoft Sidewinder Precision Pro (HID)")
        print("   -x      : test Microsoft XBox Controller Type S")
        print("   -l lang : language to report errors in (ISO 639-1)")
        print("   -w      : force the use of device requests when querying WCID descriptors")
        print("If only the vid:pid is provided, xusb attempts to run the most appropriate test")
        return 0

    version = usb.get_version()[0]
    print("Using libusb v{}.{}.{}.{}\n".format(
          version.major, version.minor, version.micro, version.nano))

    if hasattr(usb, "init_context"):
        # xusb is commonly used as a debug tool, so it's convenient to have debug output
        # during libusb.init_context().
        old_dbg_str = None
        if debug_mode:
            options = usb.init_option()
            options.option = usb.LIBUSB_OPTION_LOG_LEVEL
            options.value.ival = usb.LIBUSB_LOG_LEVEL_DEBUG
            r = usb.init_context(None, ct.byref(options), 1)
        else:
            r = usb.init_context(None, None, 0)
    else:
        # xusb is commonly used as a debug tool, so it's convenient to have debug output
        # during libusb.init(), but since we can't call on libusb.set_option() before
        # libusb.init(), we use the env variable method
        old_dbg_str = os.environ.get("LIBUSB_DEBUG", None)
        if debug_mode:
            debug_env_str = "LIBUSB_DEBUG=4"  # usb.LIBUSB_LOG_LEVEL_DEBUG
            try:
                env_var, _, env_value = debug_env_str.partition("=")
                os.environ[env_var] = env_value
            except:
                print("Unable to set debug level")
        r = usb.init(None)

    if r < 0:
        return r

    try:
        # If not set externally, and no debug option was given, use info log level
        if old_dbg_str is None and not debug_mode:
            usb.set_debug(None, usb.LIBUSB_LOG_LEVEL_INFO)
        if error_lang is not None:
            r = usb.setlocale(error_lang)
            if r < 0:
                print("Invalid or unsupported locale '{}': {}".format(
                      error_lang, usb_strerror(r)))

        test_device(VID, PID)
    finally:
        usb.exit(None)

    if debug_mode:
        #char string[256];
        string = "LIBUSB_DEBUG={}".format("" if old_dbg_str is None else old_dbg_str)

    return 0


if __name__.rpartition(".")[-1] == "__main__":
    sys.exit(main())
