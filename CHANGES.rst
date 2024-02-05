Changelog
=========

1.0.27 (2024-02-05)
-------------------
- | The API has been fully updated to version 1.0.27 (libusb v.1.0.27
  | is fully backward compatible with v.1.0.26).
- | For Windows the shared library binaries have been updated to version
  | 1.0.27. For Linux and macOS, the shared library binaries remain at
  | version 1.0.26.
- Bugfixes for options -i and -w in examples/xusb.py

1.0.26 (2024-02-05)
-------------------
- | The API has been partially updated to version 1.0.27, but still
  | only supports version 1.0.26.
- Improvements and some little bugfixes.
- Examples and tests are upgraded to 1.0.27.

1.0.26rc4 (2024-01-25)
----------------------
- Setup update (now based on tox >= 4.0).
- Cleanup.

1.0.26rc2 (2023-12-20)
----------------------
- Add linux aarch64 support.

1.0.26rc1 (2023-12-15)
----------------------
- Add support for Python 3.12
- Drop support for Python 3.7
- Add support for PyPy 3.10
- Drop support for PyPy 3.7 and 3.8
- Copyright year update.

1.0.26b5 (2022-09-10)
---------------------
- Tox configuration has been moved to pyproject.toml

1.0.26b4 (2022-08-25)
---------------------
- | Downgrade of included shared libraries for Linux:
  | libusb v.1.0.26 -> v.1.0.24 (for now based on Debian's 11 (bullseye)),
  | because of loading issues of v.1.0.26 from Debian's 12 (bookworm)
  | shared libraries.
- Setup update.

1.0.26b3 (2022-07-25)
---------------------
- Setup update (currently based mainly on pyproject.toml).
- Update for macOS (dlls are included for v.10.7+ and v.11.6+ 64bit).

1.0.26b2 (2022-07-18)
---------------------
- Upgrade for Windows: libusb v.1.0.24 -> v.1.0.26
- Update for macOS (v.11.6 64bit).
- Add support for Python 3.10 and 3.11
- Add support for PyPy 3.7, 3.8 and 3.9
- Setup update.

1.0.24b3 (2022-01-10)
---------------------
- Drop support for Python 3.6
- Copyright year update.
- Setup update.

1.0.24b1 (2021-11-10)
---------------------
- Upgrade for Windows: libusb v.1.0.23 -> v.1.0.24
- Add support for macOS (thank you very much dccote@Github!).
- Copyright year update.
- *backward incompatibility* - libusb.cfg is now a regular INI file.
- Fixes for examples (but still some examples don't work properly).
- Setup update.

1.0.23b7 (2020-11-19)
---------------------
- Ability to specify the underlying shared library programmatically.
- General update and cleanup.
- Setup update.
- Removing dependence on atpublic.
- Fixed docs setup.
- Fix for hotplugtest example.

1.0.23b1 (2020-09-15)
---------------------
- | Upgrade for Windows: libusb v.1.0.22 -> v.1.0.23
  | (partially; without libusb_wrap_sys_device, because
  |  original Windows v.1.0.23 dlls do not export this function).
- Add support for Python 3.9
- Drop support for Python 3.5
- Setup update.
- Cleanup.

1.0.22b9 (2020-01-17)
---------------------
- Added ReadTheDocs config file.
- Setup update.

1.0.22b8 (2019-11-24)
---------------------
- Upgrade for Linux: libusb x64 v.1.0.21 -> v.1.0.22
- Fix for error when the shared library is configured.
- Cleanup.

1.0.22b6 (2019-11-23)
---------------------
- Initial support for Linux (libusb v.1.0.21 x64).

1.0.22b5 (2019-11-14)
---------------------
- Drop support for Python 2
- Drop support for Python 3.4
- Add support for Python 3.8
- Setup update and cleanup.

1.0.22b4 (2019-02-15)
---------------------
- Setup improvement.
- Update required setuptools version.
- Some updates of examples.

1.0.22b2 (2018-11-08)
---------------------
- Setup improvement.
- Update required setuptools version.

1.0.22b1 (2018-03-30)
---------------------
- Upgrade to the libusb v.1.0.22
- Setup improvement.

1.0.21b4 (2018-02-26)
---------------------
- Improve and simplify setup and packaging.

1.0.21b3 (2018-02-25)
---------------------
- Setup improvement.

1.0.21b2 (2017-12-18)
---------------------
- Fix the error of platform detecting.

1.0.21b1 (2017-10-11)
---------------------
- First beta release.

1.0.21a3 (2017-08-20)
---------------------
- Next alpha release.

1.0.21a0 (2016-09-24)
---------------------
- First alpha release.

0.0.1 (2016-09-23)
------------------
- Initial release.
