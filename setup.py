# coding: utf-8

from __future__ import absolute_import

from setuptools import setup
from os.path import dirname, abspath, join as path
from codecs import open as fopen
fopen = lambda name, mode="r", open=fopen: open(name, mode, "utf-8")

setup_dir = dirname(abspath(__file__))

class about:
    exec(open(path(setup_dir, "libusb", "__about__.py")).read(), None)

setup(
    name             = about.__title__,
    version          = about.__version__,
    description      = about.__summary__,
    url              = about.__uri__,
    download_url     = about.__uri__,

    author           = about.__author__,
    author_email     = about.__email__,
    maintainer       = about.__author__,
    maintainer_email = about.__email__,
    license          = about.__license__,
    long_description = (fopen(path(setup_dir, "README.rst")).read() + "\n" +
                        fopen(path(setup_dir, "CHANGES.rst")).read()),

    python_requires  = ">=2.7.0,!=3.0.*,!=3.1.*,!=3.2.*",
    setup_requires   = ["setuptools>=30.4.0"],
    install_requires = ["setuptools>=30.4.0"],
)

# eof
