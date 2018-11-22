libusb
=======

Python binding for the *libusb* C library.

Overview
========

| Python *libusb* module is a low-level binding for *libusb* C library.
| It is an effort to allow python programs full access to the API implemented
  and provided by the well known `*libusb* <http://libusb.info>`__ library.
|
| *libusb* is a lightweight Python package, based on the *ctypes* library.
| It is fully compliant implementation of the original C *libusb* 1.0 API
  by implementing whole its functionality in a clean Python instead of C.
|
| *libusb* API 1.0 documentation can be found at:

  `libusb-1.0 API Reference <http://api.libusb.info>`__

About original libusb:
----------------------

Borrowed from the `original website <http://libusb.info>`__:

**libusb** - A cross-platform user library to access USB devices

**Overview**

**libusb** is a C library that provides generic access to USB devices.
It is intended to be used by developers to facilitate the production of
applications that communicate with USB hardware.

It is **portable**: Using a single cross-platform API, it provides access
to USB devices on Linux, OS X, Windows, Android, OpenBSD, etc.

It is **user-mode**: No special privilege or elevation is required for the
application to communicate with a device.

It is **version-agnostic**: All versions of the USB protocol, from 1.0 to 3.1
(latest), are supported.

**What platforms are supported?**

Linux, OS X, Windows, Windows CE, Android, OpenBSD/NetBSD, Haiku.

**For additional information, please consult the**
`FAQ <https://github.com/libusb/libusb/wiki/FAQ>`__
**or the** `Wiki <https://github.com/libusb/libusb/wiki>`__.

Requirements
============

- | It is fully independent package.
  | All necessary things are installed during the normal installation process.
- ATTENTION: currently works and tested only for Windows.

Installation
============

Prerequisites:

+ Python 2.7 or Python 3.4 or later

  * http://www.python.org/
  * 2.7 and 3.4 with libusb 1.0.21 are primary test environments.

+ pip and setuptools

  * http://pypi.python.org/pypi/pip
  * http://pypi.python.org/pypi/setuptools

To install run::

    python -m pip install --upgrade libusb

Development
===========

Visit `development page <https://github.com/karpierz/libusb>`__

Installation from sources:

Clone the `sources <https://github.com/karpierz/libusb>`__ and run::

    python -m pip install ./libusb

or on development mode::

    python -m pip install --editable ./libusb

Prerequisites:

+ Development is strictly based on *tox*. To install it run::

    python -m pip install tox

License
=======

  | Copyright (c) 2016-2018 Adam Karpierz
  |
  | Licensed under the zlib/libpng License
  | http://opensource.org/licenses/zlib
  | Please refer to the accompanying LICENSE file.

Authors
=======

* Adam Karpierz <adam@karpierz.net>
