# Copyright (c) 2016 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/license/zlib

# Copyright © 2001 Stephen Williams (steve@icarus.com)
# Copyright © 2001-2002 David Brownell (dbrownell@users.sourceforge.net)
# Copyright © 2008 Roger Williams (rawqux@users.sourceforge.net)
# Copyright © 2012 Pete Batard (pete@akeo.ie)
# Copyright © 2013 Federico Manzan (f.manzan@gmail.com)
#
#    This source code is free software; you can redistribute it
#    and/or modify it in source code form under the terms of the GNU
#    General Public License as published by the Free Software
#    Foundation; either version 2 of the License, or (at your option)
#    any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA

import sys
import errno
import ctypes as ct

import libusb as usb

usb_error_name = lambda status: usb.error_name(status).decode("utf-8")

FX_TYPE_UNDEFINED = -1
FX_TYPE_AN21      = 0  # Original AnchorChips parts
FX_TYPE_FX1       = 1  # Updated Cypress versions
FX_TYPE_FX2       = 2  # USB 2.0 versions
FX_TYPE_FX2LP     = 3  # Updated FX2
FX_TYPE_FX3       = 4  # USB 3.0 versions
FX_TYPE_MAX       = 5
FX_TYPE_NAMES     = ("an21", "fx", "fx2", "fx2lp", "fx3")

IMG_TYPE_UNDEFINED = -1
IMG_TYPE_HEX       = 0  # Intel HEX
IMG_TYPE_IIC       = 1  # Cypress 8051 IIC
IMG_TYPE_BIX       = 2  # Cypress 8051 BIX
IMG_TYPE_IMG       = 3  # Cypress IMG format
IMG_TYPE_MAX       = 4
IMG_TYPE_NAMES     = ("Intel HEX", "Cypress 8051 IIC", "Cypress 8051 BIX", "Cypress IMG format")

# Automatically identified devices (VID, PID, type, designation).
# TODO: Could use some validation. Also where's the FX2?
#
class fx_known_device(ct.Structure):
    _fields_ = [
    ("vid",         ct.c_uint16),
    ("pid",         ct.c_uint16),
    ("type",        ct.c_int),
    ("designation", ct.c_char_p), # const char*
]

FX_KNOWN_DEVICES = (
    fx_known_device(0x0547, 0x2122, FX_TYPE_AN21,  b"Cypress EZ-USB (2122S)"),
    fx_known_device(0x0547, 0x2125, FX_TYPE_AN21,  b"Cypress EZ-USB (2121S/2125S)"),
    fx_known_device(0x0547, 0x2126, FX_TYPE_AN21,  b"Cypress EZ-USB (2126S)"),
    fx_known_device(0x0547, 0x2131, FX_TYPE_AN21,  b"Cypress EZ-USB (2131Q/2131S/2135S)"),
    fx_known_device(0x0547, 0x2136, FX_TYPE_AN21,  b"Cypress EZ-USB (2136S)"),
    fx_known_device(0x0547, 0x2225, FX_TYPE_AN21,  b"Cypress EZ-USB (2225)"),
    fx_known_device(0x0547, 0x2226, FX_TYPE_AN21,  b"Cypress EZ-USB (2226)"),
    fx_known_device(0x0547, 0x2235, FX_TYPE_AN21,  b"Cypress EZ-USB (2235)"),
    fx_known_device(0x0547, 0x2236, FX_TYPE_AN21,  b"Cypress EZ-USB (2236)"),
    fx_known_device(0x04b4, 0x6473, FX_TYPE_FX1,   b"Cypress EZ-USB FX1"),
    fx_known_device(0x04b4, 0x8613, FX_TYPE_FX2LP, b"Cypress EZ-USB FX2LP (68013A/68014A/68015A/68016A)"),
    fx_known_device(0x04b4, 0x00f3, FX_TYPE_FX3,   b"Cypress FX3"),
)

# This file contains functions for uploading firmware into Cypress
# EZ-USB microcontrollers. These chips use control endpoint 0 and vendor
# specific commands to support writing into the on-chip SRAM. They also
# support writing into the CPUCS register, which is how we reset the
# processor after loading firmware (including the reset vector).
#
# These Cypress devices are 8-bit 8051 based microcontrollers with
# special support for USB I/O.  They come in several packages, and
# some can be set up with external memory when device costs allow.
# Note that the design was originally by AnchorChips, so you may find
# references to that vendor (which was later merged into Cypress).
# The Cypress FX parts are largely compatible with the Anchorhip ones.

# Verbosity level (default 1).
# Can be increased or decreased with options v/q
verbose = 1  # int


# return True if [addr,addr+size] includes external RAM
# for Anchorchips EZ-USB or Cypress EZ-USB FX

#static
#@annotate(addr=ct.c_uint32, size=ct.c_size_t)
def fx_is_external(addr, size) -> bool:

    # with 8KB RAM, 0x0000-0x1b3f can be written
    # we can't tell if it's a 4KB device here

    if addr <= 0x1b3f:
        return (addr + size) > 0x1b40

    # there may be more RAM; unclear if we can write it.
    # some bulk buffers may be unused, 0x1b3f-0x1f3f
    # firmware can set ISODISAB for 2KB at 0x2000-0x27ff

    return True


# return True if [addr,addr+size] includes external RAM
# for Cypress EZ-USB FX2

#static
#@annotate(addr=ct.c_uint32, size=ct.c_size_t)
def fx2_is_external(addr, size) -> bool:

    # 1st 8KB for data/code, 0x0000-0x1fff
    if addr <= 0x1fff:
        return (addr + size) > 0x2000
    # and 512 for data, 0xe000-0xe1ff
    elif addr >= 0xe000 and addr <= 0xe1ff:
        return (addr + size) > 0xe200
    # otherwise, it's certainly external
    else:
        return True


# return True if [addr,addr+size] includes external RAM
# for Cypress EZ-USB FX2LP

#static
#@annotate(addr=ct.c_uint32, size=ct.c_size_t)
def fx2lp_is_external(addr, size) -> bool:

    # 1st 16KB for data/code, 0x0000-0x3fff
    if addr <= 0x3fff:
        return (addr + size) > 0x4000
    # and 512 for data, 0xe000-0xe1ff
    elif addr >= 0xe000 and addr <= 0xe1ff:
        return (addr + size) > 0xe200
    # otherwise, it's certainly external
    else:
        return True


#*****************************************************************************#


# These are the requests (bRequest) that the bootstrap loader is expected
# to recognize.  The codes are reserved by Cypress, and these values match
# what EZ-USB hardware, or "Vend_Ax" firmware (2nd stage loader) uses.
# Cypress' "a3load" is nice because it supports both FX and FX2, although
# it doesn't have the EEPROM support (subset of "Vend_Ax").

RW_INTERNAL = 0xA0  # hardware implements this one
RW_MEMORY   = 0xA3

# Issues the specified vendor-specific write request.

#static
#@annotate(device=ct.POINTER(usb.device_handle), label=const char*)
#          ct.c_uint8 opcode, ct.c_uint32 addr,
#          const ct.POINTER(ct.c_ubyte) data, ct.c_size_t size)
def ezusb_write(device, label, opcode, addr, data, size) -> int:

    from fxload import logerror
    global verbose

    if verbose > 1:
        logerror("{}, addr {:#010x} len {:4d} ({:#06x})\n",
                 label, addr, size, size)
    status = usb.control_transfer(device,
                                  usb.LIBUSB_ENDPOINT_OUT |
                                  usb.LIBUSB_REQUEST_TYPE_VENDOR |
                                  usb.LIBUSB_RECIPIENT_DEVICE,
                                  opcode,
                                  addr & 0xFFFF, addr >> 16,
                                  ct.cast(data, ct.POINTER(ct.c_ubyte)),
                                  ct.c_uint16(size),
                                  1000)
    if status != ct.c_int(size).value:
        if status < 0:
            logerror("{}: {}\n", label, usb_error_name(status))
        else:
            logerror("{} ==> {}\n", label, status)

    if status < 0:
        ct.set_errno(errno.EIO)
        return -1
    return 0


# Issues the specified vendor-specific read request.

#static
#@annotate(device=ct.POINTER(usb.device_handle), label=const char*)
#          ct.c_uint8 opcode, ct.c_uint32 addr,
#          const ct.POINTER(ct.c_ubyte) data, ct.c_size_t size)
def ezusb_read(device, label, opcode, addr, data, size) -> int:

    from fxload import logerror
    global verbose

    if verbose > 1:
        logerror("{}, addr {:#010x} len {:4d} ({:#06x})\n",
                 label, addr, size, size)
    status = usb.control_transfer(device,
                                  usb.LIBUSB_ENDPOINT_IN |
                                  usb.LIBUSB_REQUEST_TYPE_VENDOR |
                                  usb.LIBUSB_RECIPIENT_DEVICE,
                                  opcode,
                                  addr & 0xFFFF, addr >> 16,
                                  ct.cast(data, ct.POINTER(ct.c_ubyte)),
                                  ct.c_uint16(size),
                                  1000)
    if status != ct.c_int(size).value:
        if status < 0:
            logerror("{}: {}\n", label, usb_error_name(status))
        else:
            logerror("{} ==> {}\n", label, status)

    if status < 0:
        ct.set_errno(errno.EIO)
        return -1
    return 0


# Modifies the CPUCS register to stop or reset the CPU.
# Returns False on error.

#static
#@annotate(device=ct.POINTER(usb.device_handle), addr=ct.c_uint32)
def ezusb_cpucs(device, addr, do_run: bool) -> bool:

    from fxload import logerror
    global verbose

    data = ct.c_uint8(0x00 if do_run else 0x01)

    if verbose:
        logerror("{}\n", "stop CPU" if data else "reset CPU")
    status = usb.control_transfer(device,
                                  usb.LIBUSB_ENDPOINT_OUT |
                                  usb.LIBUSB_REQUEST_TYPE_VENDOR |
                                  usb.LIBUSB_RECIPIENT_DEVICE,
                                  RW_INTERNAL,
                                  addr & 0xFFFF, addr >> 16,
                                  ct.byref(data), 1,
                                  1000);
    if (status != 1 and
        # We may get an I/O error from libusb as the device disappears
        (not do_run or status != usb.LIBUSB_ERROR_IO)):
        mesg = "can't modify CPUCS"
        if status < 0:
            logerror("{}: {}\n", mesg, usb_error_name(status))
        else:
            logerror("{}\n", mesg)
        return False
    else:
        return True


# Send an FX3 jump to address command
# Returns False on error.

#static
#@annotate(device=ct.POINTER(usb.device_handle), addr=ct.c_uint32)
def ezusb_fx3_jump(device, addr) -> bool:

    from fxload import logerror
    global verbose

    if verbose:
        logerror("transfer execution to Program Entry at {:#010x}\n", addr)
    status = usb.control_transfer(device,
                                  usb.LIBUSB_ENDPOINT_OUT |
                                  usb.LIBUSB_REQUEST_TYPE_VENDOR |
                                  usb.LIBUSB_RECIPIENT_DEVICE,
                                  RW_INTERNAL,
                                  addr & 0xFFFF, addr >> 16,
                                  NULL, 0,
                                  1000)
    # We may get an I/O error from libusb as the device disappears
    if status != 0 and status != usb.LIBUSB_ERROR_IO:
        mesg = "failed to send jump command"
        if status < 0:
            logerror("{}: {}\n", mesg, usb_error_name(status))
        else:
            logerror("{}\n", mesg)
        return False
    else:
        return True


#*****************************************************************************#


# Parse an Intel HEX image file and invoke the poke() function on the
# various segments to implement policies such as writing to RAM (with
# a one or two stage loader setup, depending on the firmware) or to
# EEPROM (two stages required).
#
# image       - the hex image file
# context     - for use by poke()
# is_external - if non-null, used to check which segments go into
#               external memory (writable only by software loader)
# poke        - called with each memory segment; errors indicated
#               by returning negative values.
#
# Caller is responsible for halting CPU as needed, such as when
# overwriting a second stage loader.

#static
#@annotate(image=FILE*, context=void*,
#          is_external=bool (*)(ct.c_uint32 addr, ct.c_size_t len),
#          poke=int (*)(void* context, ct.c_uint32 addr, bool external,
#                       const ct.POINTER(ct.c_ubyte) data, ct.c_size_t len))
def parse_ihex(image, context, is_external, poke) -> int:

    from fxload import logerror
    global verbose

    data = (ct.c_ubyte * 1023)()

    # Read the input file as an IHEX file, and report the memory segments
    # as we go.  Each line holds a max of 16 bytes, but uploading is
    # faster (and EEPROM space smaller) if we merge those lines into larger
    # chunks.  Most hex files keep memory segments together, which makes
    # such merging all but free.  (But it may still be worth sorting the
    # hex files to make up for undesirable behavior from tools.)
    #
    # Note that EEPROM segments max out at 1023 bytes; the upload protocol
    # allows segments of up to 64 KBytes (more than a loader could handle).

    data_len  = 0  # ct.c_size_t
    data_addr = ct.c_uint32(0)
    external  = False  # bool

    first_line = True
    while True:

        buf = bytearray(b"\0"* 512)
        try:
            image.readinto(buf)
        except:
            logerror("EOF without EOF record!\n")
            break

        # EXTENSION: "# comment-till-end-of-line", for copyrights etc
        if buf[0] == ord('#'):
            continue

        if buf[0] != ord(':'):
            logerror("not an ihex record: {}", buf)
            return -2

        # ignore any newline
        #cp # char*
        cp = strchr(buf, '\n')
        if cp != NULL:
            cp[0] = 0

        if verbose >= 3:
            logerror("** LINE: {}\n", buf)

        # Read the length field (up to 16 bytes)
        tmp = buf[3]; buf[3] = 0
        #size # ct.c_size_t
        size = size_t(strtoul(buf[1:], NULL, 16))
        buf[3] = tmp

        # Read the target offset (address up to 64KB)
        tmp = buf[7]; buf[7] = 0
        #off # unsigned
        off = unsigned_int(strtoul(buf[3:], NULL, 16))
        buf[7] = tmp

        # Initialize data_addr
        if first_line:
            data_addr  = off
            first_line = False

        # Read the record type
        tmp = buf[9]; buf[9] = 0
        #rec_type # char
        rec_type = char(strtoul(buf[7:], NULL, 16))
        buf[9] = tmp

        # If this is an EOF record, then make it so.
        if rec_type == 1:
            if verbose >= 2:
                logerror("EOF on hexfile\n")
            break;

        if rec_type != 0:
            logerror("unsupported record type: {:d}\n", rec_type)
            return -3

        if size * 2 + 11 > strlen(buf):
            logerror("record too short?\n")
            return -4

        # FIXME check for _physically_ contiguous not just virtually
        # e.g. on FX2 0x1f00-0x2100 includes both on-chip and external
        # memory so it's not really contiguous

        # flush the saved data if it's not contiguous,
        # or when we've buffered as much as we can.

        if (data_len != 0 and (off != (data_addr + data_len) or
                               # not merge or
                               (data_len + size) > ct.sizeof(data))):
            if is_external: external = is_external(data_addr, data_len)
            rc = poke(context, data_addr, external, data, data_len)
            if rc < 0:
                return -1
            data_addr = off
            data_len  = 0

        # append to saved data, flush later
        cp = buf + 9
        for idx in range(size):
            tmp = cp[2]; cp[2] = 0
            data[data_len + idx] = ct.c_uint8(strtoul(cp, NULL, 16))
            cp[2] = tmp
            cp += 2

        data_len += size

    # flush any data remaining
    if data_len != 0:
        if is_external: external = is_external(data_addr, data_len)
        rc = poke(context, data_addr, external, data, data_len)
        if rc < 0:
            return -1

    return 0


# Parse a binary image file and write it as is to the target.
# Applies to Cypress BIX images for RAM or Cypress IIC images
# for EEPROM.
#
# image       - the BIX image file
# context     - for use by poke()
# is_external - if non-null, used to check which segments go into
#               external memory (writable only by software loader)
# poke        - called with each memory segment; errors indicated
#               by returning negative values.
#
# Caller is responsible for halting CPU as needed, such as when
# overwriting a second stage loader.

#static
#@annotate(image=FILE*, context=void*,
#          is_external=bool (*)(ct.c_uint32 addr, ct.c_size_t len),
#          poke=int (*)(void* context, ct.c_uint32 addr, bool external,
#                       const ct.POINTER(ct.c_ubyte) data, ct.c_size_t len))
def parse_bin(image, context, is_external, poke) -> int:

    data = (ct.c_ubyte * 4096)()

    data_len  = 0  # ct.c_size_t
    data_addr = ct.c_uint32(0)
    external  = False  # bool

    while True:

        data_len = image.readinto(data)
        if data_len == 0:
            break

        if is_external: external = is_external(data_addr, data_len)
        rc = poke(context, data_addr, external, data, data_len)
        if rc < 0:
            return -1
        data_addr += data_len

    return 0 if feof(image) else -1


# Parse a Cypress IIC image file and invoke the poke() function on the
# various segments for writing to RAM
#
# image       - the IIC image file
# context     - for use by poke()
# is_external - if non-null, used to check which segments go into
#               external memory (writable only by software loader)
# poke        - called with each memory segment; errors indicated
#               by returning negative values.
#
# Caller is responsible for halting CPU as needed, such as when
# overwriting a second stage loader.

#static
#@annotate(image=FILE*, context=void*,
#          is_external=bool (*)(ct.c_uint32 addr, ct.c_size_t len),
#          poke=int (*)(void* context, ct.c_uint32 addr, bool external,
#                       const ct.POINTER(ct.c_ubyte) data, ct.c_size_t len))
def parse_iic(image, context, is_external, poke) -> int:

    from fxload import logerror

    data = (ct.c_ubyte * 4096)()
    block_header = (ct.c_uint8 * 4)()

    data_len  = 0  # ct.c_size_t
    data_addr = ct.c_uint32(0)
    external  = False  # bool

    #long file_size
    #long initial_pos
    initial_pos = ftell(image)
    if initial_pos < 0:
        return -1
    if fseek(image, 0, SEEK_END) != 0:
        return -1
    file_size = ftell(image);
    if fseek(image, initial_pos, SEEK_SET) != 0:
        return -1
    while True:
        # Ignore the trailing reset IIC data (5 bytes)
        if ftell(image) >= (file_size - 5):
            break

        if image.readinto(block_header) != ct.sizeof(block_header):
            logerror("unable to read IIC block header\n")
            return -1

        data_len  = (block_header[0] << 8) + block_header[1]
        data_addr = (block_header[2] << 8) + block_header[3]
        if data_len > ct.sizeof(data):
            # If this is ever reported as an error, switch to using malloc/realloc
            logerror("IIC data block too small - please report this error to libusb.info\n")
            return -1

        #read_len  # ct.c_size_t
        read_len = image.fread(data, data_len)
        if read_len != data_len:
            logerror("read error\n")
            return -1

        if is_external: external = is_external(data_addr, data_len)
        rc = poke(context, data_addr, external, data, data_len)
        if rc < 0:
            return -1

    return 0


# the parse call will be selected according to the image type
#static
_parse = [
   parse_ihex,
   parse_iic,
   parse_bin,
   None
]


#*****************************************************************************#


# For writing to RAM using a first (hardware) or second (software)
# stage loader and 0xA0 or 0xA3 vendor requests

ram_mode = ct.c_int
(
    _undef,
    internal_only,  # hardware first-stage loader
    skip_internal,  # first phase, second-stage loader
    skip_external,  # second phase, second-stage loader
) = (0, 1, 2, 3)

class ram_poke_context(ct.Structure):
    _fields_ = [
    ("device", ct.POINTER(usb.device_handle)),
    ("mode",   ram_mode),
    ("total",  ct.c_size_t),
    ("count",  ct.c_size_t),
]

RETRY_LIMIT = 5

#static
#@annotate(context=void*, addr=ct.c_uint32, external=bool,
#          data=const ct.POINTER(ct.c_ubyte), size=ct.c_size_t)
def ram_poke(context, addr, external, data, size) -> int:

    from fxload import logerror

    ctx = ct.cast(context, ct.POINTER(ram_poke_context))[0]

    ctx_mode = ctx.mode
    if ctx_mode == internal_only:    # CPU should be stopped
        if external:
            logerror("can't write {} bytes external memory at {:#010x}\n", size, addr)
            ct.set_errno(errno.EINVAL)
            return -1
    elif ctx_mode == skip_internal:  # CPU must be running
        if not external:
            if verbose >= 2:
                logerror("SKIP on-chip RAM, {} bytes at {:#010x}\n", size, addr)
            return 0
    elif ctx_mode == skip_external:  # CPU should be stopped
        if external:
            if verbose >= 2:
                logerror("SKIP external RAM, {} bytes at {:#010x}\n", size, addr)
            return 0
    elif ctx_mode == _undef:
        logerror("bug\n")
        ct.set_errno(errno.EDOM)
        return -1
    else:
        logerror("bug\n")
        ct.set_errno(errno.EDOM)
        return -1

    ctx.total += size
    ctx.count += 1

    # Retry this till we get a real error. Control messages are not
    # NAKed (just dropped) so time out means is a real problem.

    retry = 0
    while True:
        rc = ezusb_write(ctx.device,
                         "write external" if external else "write on-chip",
                         RW_MEMORY if external else RW_INTERNAL,
                         addr, data, size)
        if rc >= 0 or retry >= RETRY_LIMIT:
            break
        if rc != usb.LIBUSB_ERROR_TIMEOUT:
            break
        retry += 1

    return rc


# Load a Cypress Image file into target RAM.
# See http://www.cypress.com/?docID=41351 (AN76405 PDF) for more info.

#static
#@annotate(device=ct.POINTER(usb.device_handle), path=str)
def fx3_load_ram(device, path) -> int:

    from fxload import logerror
    global verbose

    bBuf  = ct.POINTER(ct.c_ubyte)
    hBuf  = (ct.c_ubyte * 4)()
    blBuf = (ct.c_ubyte * 4)()
    rBuf  = (ct.c_ubyte * 4096)()

    try:
        image = open(path, "rb")
    except:
        logerror("unable to open '{}' for input\n", path)
        return -2

    if verbose:
        logerror("open firmware image {} for RAM upload\n", path)

    with image:

        # Read header
        if image.readinto(hBuf) != ct.sizeof(hBuf):
            logerror("could not read image header")
            return -3

        # check "CY" signature byte and format
        if hBuf[0] != 'C' or hBuf[1] != 'Y':
            logerror("image doesn't have a CYpress signature\n")
            return -3

        # Check bImageType
        bImageType = hBuf[3]
        if bImageType == 0xB0:
            if verbose:
                logerror("normal FW binary {} image with checksum\n", "data" if hBuf[2] & 0x01 else "executable")
        elif bImageType == 0xB1:
            logerror("security binary image is not currently supported\n")
            return -3
        elif bImageType == 0xB2:
            logerror("VID:PID image is not currently supported\n")
            return -3
        else:
            logerror("invalid image type {:#04X}\n", hBuf[3])
            return -3

        # Read the bootloader version
        if verbose:
            if ezusb_read(device, "read bootloader version", RW_INTERNAL, 0xFFFF0020, blBuf, 4) < 0:
                logerror("Could not read bootloader version\n")
                return -8
            logerror("FX3 bootloader version: {:#04X}{:02X}{:02X}{:02X}\n",
                     blBuf[3], blBuf[2], blBuf[1], blBuf[0])

        if verbose:
            logerror("writing image...\n")

        dLength  = ct.c_uint32()
        dAddress = ct.c_uint32()
        dCheckSum = 0  # ct.c_uint32
        while True:
            if ((image.fread(ct.byref(dLength),  ct.sizeof(ct.c_uint32)) != ct.sizeof(ct.c_uint32)) or  # read dLength
                (image.fread(ct.byref(dAddress), ct.sizeof(ct.c_uint32)) != ct.sizeof(ct.c_uint32))):   # read dAddress
                logerror("could not read image")
                return -3
            if dLength == 0:
                break # done

            # coverity[tainted_data]
            try:
                dImageBuf = (ct.c_uint32 * dLength)()
                ct.memset(dImageBuf, b"\0", dLength * ct.sizeof(ct.c_uint32))
            except:
                logerror("could not allocate buffer for image chunk\n")
                return -4

            # read sections
            if image.fread(dImageBuf, ct.sizeof(ct.c_uint32) * dLength) != ct.sizeof(ct.c_uint32) * dLength:
                logerror("could not read image")
                return -3

            for i in range(dLength):
                dCheckSum += dImageBuf[i]

            dLength <<= 2  # convert to Byte length
            bBuf = ct.cast(dImageBuf, ct.POINTER(ct.c_ubyte))
            while dLength > 0:

               #dLen  # ct.c_uint32
                dLen = min(dLength, 4096)  # 4K max
                if (ezusb_write(device, "write firmware", RW_INTERNAL, dAddress, bBuf, dLen) < 0 or
                    ezusb_read (device, "read firmware",  RW_INTERNAL, dAddress, rBuf, dLen) < 0):
                    logerror("R/W error\n")
                    return -5

                # Verify data: rBuf with bBuf
                for i in range(dLen):
                    if rBuf[i] != bBuf[i]:
                        logerror("verify error")
                        return -6

                dLength  -= dLen
                bBuf     += dLen
                dAddress += dLen

        # read pre-computed checksum data
        dExpectedCheckSum = ct.c_uint32()
        if (image.fread(ct.byref(dExpectedCheckSum), ct.sizeof(ct.c_uint32)) != ct.sizeof(ct.c_uint32) or
            dCheckSum != dExpectedCheckSum):
            logerror("checksum error\n")
            return -7

        # transfer execution to Program Entry
        if not ezusb_fx3_jump(device, dAddress):
            return -6

    return 0


# This function uploads the firmware from the given file into RAM.
# Stage == 0 means this is a single stage load (or the first of
# two stages).  Otherwise it's the second of two stages; the
# caller having preloaded the second stage loader.
#
# The target processor is reset at the end of this upload.

#@annotate(device=ct.POINTER(usb.device_handle), path=str, fx_type=ct.c_int, img_type=ct.c_int, stage=ct.c_int)
def ezusb_load_ram(device, path, fx_type, img_type, stage) -> int:

    # Load a firmware file into target RAM. device is the open libusb
    # device, and the path is the name of the source file. Open the file,
    # parse the bytes, and write them in one or two phases.
    #
    # If stage == 0, this uses the first stage loader, built into EZ-USB
    # hardware but limited to writing on-chip memory or CPUCS.  Everything
    # is written during one stage, unless there's an error such as the image
    # holding data that needs to be written to external memory.
    #
    # Otherwise, things are written in two stages.  First the external
    # memory is written, expecting a second stage loader to have already
    # been loaded.  Then file is re-parsed and on-chip memory is written.

    from fxload import logerror
    global verbose

    if fx_type == FX_TYPE_FX3:
        return fx3_load_ram(device, path)

    try:
        image = open(path, "rb")
    except:
        logerror("{}: unable to open for input.\n", path)
        return -2

    if verbose > 1:
        logerror("open firmware image {} for RAM upload\n", path)

    with image:

        if img_type == IMG_TYPE_IIC:
            iic_header = (ct.c_uint8 * 8)()
            if (image.readinto(iic_header) != ct.sizeof(iic_header) or
                ((fx_type == FX_TYPE_FX2LP or
                  fx_type == FX_TYPE_FX2) and iic_header[0] != 0xC2) or
                (fx_type == FX_TYPE_AN21  and iic_header[0] != 0xB2) or
                (fx_type == FX_TYPE_FX1   and iic_header[0] != 0xB6)):
                logerror("IIC image does not contain executable code - cannot load to RAM.\n")
                return -1

        cpucs_addr  = None
        is_external = None # bool (*)(ct.c_uint32 off, ct.c_size_t len)
        # EZ-USB original/FX and FX2 devices differ, apart from the 8051 core
        if fx_type == FX_TYPE_FX2LP:
            cpucs_addr  = 0xe600
            is_external = fx2lp_is_external
        elif fx_type == FX_TYPE_FX2:
            cpucs_addr  = 0xe600
            is_external = fx2_is_external
        else:
            cpucs_addr  = 0x7f92
            is_external = fx_is_external

        ctx = ram_poke_context()
        # use only first stage loader?
        if stage == 0:
            ctx.mode = internal_only
            # if required, halt the CPU while we overwrite its code/data
            if cpucs_addr is not None and not ezusb_cpucs(device, cpucs_addr, False):
                return -1
            # 2nd stage, first part? loader was already uploaded
        else:
            ctx.mode = skip_internal
            # let CPU run; overwrite the 2nd stage loader later
            if verbose:
                logerror("2nd stage: write external memory\n")
        # scan the image, first (maybe only) time
        ctx.device = device
        ctx.total  = 0
        ctx.count  = 0
        status = _parse[img_type](image, ct.byref(ctx), is_external, ram_poke)
        if status < 0:
            logerror("unable to upload {}\n", path)
            return status

        # second part of 2nd stage: rescan
        # TODO: what should we do for non HEX images there?
        if stage:
            ctx.mode = skip_external
            # if needed, halt the CPU while we overwrite the 1st stage loader
            if cpucs_addr is not None and not ezusb_cpucs(device, cpucs_addr, False):
                return -1
            # at least write the interrupt vectors (at 0x0000) for reset!
            rewind(image)
            if verbose:
                logerror("2nd stage: write on-chip memory\n")
            status = parse_ihex(image, ct.byref(ctx), is_external, ram_poke)
            if status < 0:
                logerror("unable to completely upload {}\n", path)
                return status

        if verbose and ctx.count != 0:
            logerror("... WROTE: {} bytes, {} segments, avg {}\n",
                     ctx.total, ctx.count, ctx.total // ctx.count)

        # if required, reset the CPU so it runs what we just uploaded
        if cpucs_addr is not None and not ezusb_cpucs(device, cpucs_addr, True):
            return -1

    return 0


# This function uploads the firmware from the given file into EEPROM.
# This uses the right CPUCS address to terminate the EEPROM load with
# a reset command where FX parts behave differently than FX2 ones.
# The configuration byte is as provided here (zero for an21xx parts)
# and the EEPROM type is set so that the microcontroller will boot
# from it.
#
# The caller must have preloaded a second stage loader that knows
# how to respond to the EEPROM write request.

#@annotate(device=ct.POINTER(usb.device_handle), path=str, fx_type=ct.c_int, img_type=ct.c_int, config=ct.c_int)
def ezusb_load_eeprom(device, path, fx_type, img_type, config) -> int:
    raise NotImplementedError()
