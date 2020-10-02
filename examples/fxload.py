# Copyright (c) 2016-2020 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/licenses/Zlib

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
import os
import getopt
import ctypes as ct
import libusb as usb
from libusb._platform import defined
from ezusb import FX_KNOWN_DEVICES, FX_TYPE_MAX, FX_TYPE_NAMES, IMG_TYPE_NAMES, FX_TYPE_UNDEFINED
from ezusb import ezusb_load_ram
from ezusb import verbose

if not defined("_WIN32") or defined("__CYGWIN__"):
    #include <syslog.h>
    dosyslog = False  # bool

if not defined("FXLOAD_VERSION"):
    FXLOAD_VERSION =" (libusb)" # __DATE__ + " (libusb)"


def logerror(fmt, *args):

    if (not defined("_WIN32") or defined("__CYGWIN__")) and dosyslog:
        ap = va_list();
        va_start(ap, fmt);
        vsyslog(LOG_ERR, fmt, ap);
        va_end(ap);
    else:
        print(fmt.format(*args), file=sys.stderr, end="")


def print_usage(error_code):

    print("\nUsage: fxload [-v] [-V] [-t type] [-d vid:pid] [-p bus,addr] [-s loader] -i firmware\n"
          "  -i <path>       -- Firmware to upload\n"
          "  -s <path>       -- Second stage loader\n"
          "  -t <type>       -- Target type: an21, fx, fx2, fx2lp, fx3\n"
          "  -d <vid:pid>    -- Target device, as an USB VID:PID\n"
          "  -p <bus,addr>   -- Target device, as a libusb bus number and device address path\n"
          "  -v              -- Increase verbosity\n"
          "  -q              -- Decrease verbosity (silent mode)\n"
          "  -V              -- Print program version", file=sys.stderr)
    return error_code


def main(argv=sys.argv):

    global verbose

    FIRMWARE = 0
    LOADER   = 1
    known_devices = FX_KNOWN_DEVICES

    paths = [None, None]  # [const char*]
    device_id   = None  # const char*
    device_path = os.environ.get("DEVICE", None)
    target_type = None  # const char*
    fx_names  = FX_TYPE_NAMES
    img_names = IMG_TYPE_NAMES
    fx_type   = FX_TYPE_UNDEFINED  # int
    img_types = [0] * len(paths)  # [int]
   #opt;          # int
   #status;       # int
   #ext;          # const char*
   #i, j;         # unsigned int
    vid = 0       # unsigned
    pid = 0       # unsigned
    busnum  = 0   # unsigned
    devaddr = 0   # unsigned
   #_busnum;      # unsigned
   #_devaddr;     # unsigned
    dev    = ct.POINTER(usb.device)()
    devs   = ct.POINTER(ct.POINTER(usb.device))()
    device = ct.POINTER(usb.device_handle)()
    desc   = usb.device_descriptor()

    try:
        opts, args = getopt.getopt(argv[1:], "qvV?hd:p:i:I:s:S:t:")
    except getopt.GetoptError:
        return print_usage(-1)

    for opt, optarg in opts:
        if opt == "-d":
            device_id = optarg
            if sscanf(device_id, "%x:%x" , ct.byref(vid), ct.byref(pid)) != 2:
                print("please specify VID & PID as \"vid:pid\" in hexadecimal format", file=sys.stderr)
                return -1
        elif opt == "-p":
            device_path = optarg
            if sscanf(device_path, "%u,%u", ct.byref(busnum), ct.byref(devaddr)) != 2:
                print("please specify bus number & device number as \"bus,dev\" in decimal format", file=sys.stderr)
                return -1
        elif opt in ("-i", "-I"):
            paths[FIRMWARE] = optarg
        elif opt in ("-s", "-S"):
            paths[LOADER] = optarg
        elif opt == "-V":
            print(FXLOAD_VERSION)
            return 0
        elif opt == "-t":
            target_type = optarg
        elif opt == "-v":
            verbose += 1
        elif opt == "-q":
            verbose -= 1
        elif opt in ("-?", "-h"):
            return print_usage(-1)
        else:
            return print_usage(-1)

    if paths[FIRMWARE] is None:
        logerror("no firmware specified!\n")
        return print_usage(-1)

    if device_id is not None and device_path is not None:
        logerror("only one of -d or -p can be specified\n")
        return print_usage(-1)

    # determine the target type
    if target_type is not None:
        for i in range(FX_TYPE_MAX):
            if fx_names[i] == target_type:
                fx_type = i
                break
        else:
            logerror("illegal microcontroller type: {}\n", target_type)
            return print_usage(-1)

    # open the device using libusb
    status = usb.init(None)
    if status < 0:
        logerror("usb.init() failed: {}\n", usb.error_name(status))
        return -1

    try:
        usb.set_option(None, usb.LIBUSB_OPTION_LOG_LEVEL, verbose)

        # try to pick up missing parameters from known devices
        if target_type is None or device_id is None or device_path is not None:

            if usb.get_device_list(None, ct.byref(devs)) < 0:
                logerror("libusb.get_device_list() failed: {}\n", usb.error_name(status))
                return -1

            i = 0
            while True:
                dev = devs[i]
                if not dev:
                    usb.free_device_list(devs, 1)
                    logerror("could not find a known device - please specify type and/or vid:pid and/or bus,dev\n")
                    return print_usage(-1)

                _busnum  = usb.get_bus_number(dev)
                _devaddr = usb.get_device_address(dev)
                if target_type is not None and device_path is not None:
                    # if both a type and bus,addr were specified, we just need to find our match
                    if (usb.get_bus_number(dev)     == busnum and
                        usb.get_device_address(dev) == devaddr):
                        break
                else:
                    status = usb.get_device_descriptor(dev, ct.byref(desc))
                    if status >= 0:

                        if verbose >= 3:
                            logerror("examining {:04x}:{:04x} ({},{})\n",
                                     desc.idVendor, desc.idProduct, _busnum, _devaddr)

                        if_break = False
                        for known_device in known_devices:
                            if (desc.idVendor  == known_device.vid and
                                desc.idProduct == known_device.pid):
                                if (# nothing was specified
                                    (target_type is None and device_id is None and device_path is None) or
                                    # vid:pid was specified and we have a match
                                    (target_type is None and device_id is not None and vid == desc.idVendor and pid == desc.idProduct) or
                                    # bus,addr was specified and we have a match
                                    (target_type is None and device_path is not None and busnum == _busnum and devaddr == _devaddr) or
                                    # type was specified and we have a match
                                    (target_type is not None and device_id is None and device_path is None and fx_type == known_device.type)):
                                    fx_type = known_device.type
                                    vid = desc.idVendor
                                    pid = desc.idProduct
                                    busnum  = _busnum
                                    devaddr = _devaddr
                                    if_break = True
                                    break
                        if if_break:
                            if verbose:
                                logerror("found device '{}' [{:04x}:{:04x}] ({},{})\n",
                                         known_device.designation, vid, pid, busnum, devaddr)
                            break
                i += 1

            status = usb.open(dev, ct.byref(device))
            usb.free_device_list(devs, 1)
            if status < 0:
                logerror("usb.open() failed: {}\n", usb.error_name(status))
                return -1

        elif device_id is not None:

            device = usb.open_device_with_vid_pid(None, ct.c_uint16(vid), ct.c_uint16(pid))
            if not device:
                logerror("usb.open() failed\n")
                return -1

        # We need to claim the first interface
        usb.set_auto_detach_kernel_driver(device, 1)
        status = usb.claim_interface(device, 0)
        if status != usb.LIBUSB_SUCCESS:
            usb.close(device)
            logerror("libusb.claim_interface failed: {}\n", usb.error_name(status))
            return -1

        if verbose:
            logerror("microcontroller type: {}\n", fx_names[fx_type])

        for i, path in enumerate(paths):
            if path is not None:
                ext = path[-4:]
                if ext.lower() == ".hex" or ext == ".ihx":
                    img_types[i] = IMG_TYPE_HEX
                elif ext.lower() == ".iic":
                    img_types[i] = IMG_TYPE_IIC
                elif ext.lower() == ".bix":
                    img_types[i] = IMG_TYPE_BIX
                elif ext.lower() == ".img":
                    img_types[i] = IMG_TYPE_IMG
                else:
                    logerror("{} is not a recognized image type\n", path)
                    return -1
            if verbose and path is not None:
                logerror("{}: type {}\n", path, img_names[img_types[i]])

        if paths[LOADER] is None:
            # single stage, put into internal memory
            if verbose > 1:
                logerror("single stage: load on-chip memory\n")
            status = ezusb_load_ram(device, paths[FIRMWARE], fx_type, img_types[FIRMWARE], 0)
        else:
            # two-stage, put loader into internal memory
            if verbose > 1:
                logerror("1st stage: load 2nd stage loader\n")
            status = ezusb_load_ram(device, paths[LOADER], fx_type, img_types[LOADER], 0)
            if status == 0:
                # two-stage, put firmware into internal memory
                if verbose > 1:
                    logerror("2nd state: load on-chip memory\n")
                status = ezusb_load_ram(device, paths[FIRMWARE], fx_type, img_types[FIRMWARE], 1)

        usb.release_interface(device, 0)
        usb.close(device)
    finally:
        usb.exit(None)

    return status


sys.exit(main())
