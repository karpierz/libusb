# flake8-in-file-ignores: noqa: F401,F403,F821

# Copyright (c) 2016 Adam Karpierz
# SPDX-License-Identifier: Zlib

from .__about__ import * ; del __about__
from . import __config__ ; del __config__
from .__config__ import set_config as config

from ._libusb import * ; del _libusb
