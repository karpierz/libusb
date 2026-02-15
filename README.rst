libusb
======

Python binding for the *libusb* C library.

Overview
========

| Python |package_bold| module is a low-level binding for *libusb* C library.
| It is an effort to allow python programs full access to the API implemented
  and provided by the well known `*libusb* <https://libusb.info/>`__ library.

`PyPI record`_.

`Documentation`_.

| |package_bold| is a lightweight Python package, based on the *ctypes* library.
| It is fully compliant implementation of the original C *libusb* 1.0 API
  by implementing whole its functionality in a clean Python instead of C.
|
| *libusb* API 1.0 documentation can be found at:

  `libusb-1.0 API Reference <https://libusb.info/>`__ on Documentation.

|package_bold| uses the underlying *libusb* C shared library as specified in
libusb.cfg (included libusb-X.X.* is the default), but there is also ability
to specify it programmatically by one of the following ways:

.. code:: python

  import libusb
  libusb.config(LIBUSB="libusb C shared library absolute path")
  # or
  libusb.config(LIBUSB=None)  # included libusb-X.X.* will be used

About original libusb:
----------------------

Borrowed from the `original website <https://libusb.info/>`__:

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

- | It is a fully independent package.
  | All necessary things are installed during the normal installation process.
- ATTENTION: currently fully tested only for Windows.

Installation
============

Prerequisites:

+ Python 3.10 or higher

  * https://www.python.org/
  * with C libusb 1.0.29 is a primary test environment.

+ pip

  * https://pypi.org/project/pip/

To install run:

  .. parsed-literal::

    python -m pip install --upgrade |package|

Development
===========

Prerequisites:

+ Development is strictly based on *nox*. To install it run::

    python -m pip install --upgrade nox

Visit `Development page`_.

Installation from sources:

clone the sources:

  .. parsed-literal::

    git clone |respository| |package|

and run:

  .. parsed-literal::

    python -m pip install ./|package|

or on development mode:

  .. parsed-literal::

    python -m pip install --editable ./|package|

License
=======

  | |copyright|
  | Licensed under the zlib/libpng License
  | https://opensource.org/license/zlib
  | Please refer to the accompanying LICENSE file.

Authors
=======

* Adam Karpierz <adam@karpierz.net>

Sponsoring
==========

| If you would like to sponsor the development of this project, your contribution
  is greatly appreciated.
| As I am now retired, any support helps me dedicate more time to maintaining and
  improving this work.

`Donate`_

.. |package| replace:: libusb
.. |package_bold| replace:: **libusb**
.. |copyright| replace:: Copyright (c) 2016-2026 Adam Karpierz
.. |respository| replace:: https://github.com/karpierz/libusb
.. _Development page: https://github.com/karpierz/libusb
.. _PyPI record: https://pypi.org/project/libusb/
.. _Documentation: https://karpierz.github.io/libusb/
.. _Donate: https://www.paypal.com/donate/?hosted_button_id=FX8L7CJUGLW7S
.. _USB Vendors: https://devicehunt.com/all-usb-vendors
