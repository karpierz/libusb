# Copyright (c) 2016 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/license/zlib

# libusb example program to manipulate U.are.U 4000B fingerprint scanner.
# Copyright © 2007 Daniel Drake <dsd@gentoo.org>
# Copyright © 2016 Nathan Hjelm <hjelmn@mac.com>
# Copyright © 2020 Chris Dickens <christopher.a.dickens@gmail.com>
#
# Basic image capture program only, does not consider the powerup quirks or
# the fact that image encryption may be enabled. Not expected to work
# flawlessly all of the time.
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

DPFP_THREADED = True

from dpfp import *


if __name__.rpartition(".")[-1] == "__main__":
    sys.exit(main())
