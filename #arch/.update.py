""" """
import sys
if sys.version_info < (3,14):
    raise AssertionError("Python version 3.14 or higher is required.")
from itertools import chain
from urllib.parse import urlparse
import re
import requests
import bs4
from utlx import module_path, Path
import patoolib

here = Path(module_path())

PKG_NAME        = "libusb"
CONDA_VERSION   = "1.0.29"
DEB_VERSION     = "1.0.29"
CONDA_BUILD_NO  = "0"
DEB_SO_NO       = "1.0"
DEB_SO_BUILD_NO = "0"
DEB_BUILD_NO    = "2"

conda_channel = "main"
conda_type    = "conda"
conda_pkg_url = (f"https://anaconda.org/conda-forge/{PKG_NAME}/files/manage?"
                 f"channel={conda_channel}&type={conda_type}&version={CONDA_VERSION}")

conda_main_url = "{}://{}".format(*urlparse(conda_pkg_url))

conda_platforms = (
    "win-64",
    "win-arm64",
    "linux-64",      
    "linux-aarch64",
    "linux-ppc64le",
    "osx-64",
    "osx-arm64",
)

debian_main_url = "http://ftp.debian.org/debian/pool/main"
debian_pkg_url  = f"{debian_main_url}/libu/{PKG_NAME}-{DEB_SO_NO}"

debian_archs = (
    "amd64",
    "i386",
    "arm64",
    "armhf",
    #"armel",
    "ppc64el",
    #"mips64el",
    "riscv64",
    "s390x",
)

html = requests.get(conda_pkg_url, stream=True).text
soup = bs4.BeautifulSoup(html, "html.parser")

for plat in conda_platforms:
    subdir = here/plat
    subdir.mkdir()
    subdir.cleardir()

    pattern = re.compile(rf"{plat}/{PKG_NAME}-{CONDA_VERSION}-.+_{CONDA_BUILD_NO}\.conda")
    tag = soup.find("a", string=pattern)
    download_url = conda_main_url + tag["href"]

    conda_pkg = subdir/f"{PKG_NAME}.conda"
    conda_pkg.write_bytes(requests.get(download_url, stream=True).content)

    conda_pkg.unpack_archive(subdir, format="zip")
    #patoolib.extract_archive(str(conda_pkg), outdir=str(subdir))

    for zstd in subdir.glob("*.zst"):
        zstd.unpack_archive(subdir, format="zstdtar")

    conda_pkg.unlink()
    for item in chain(subdir.glob("*.conda"),
                      subdir.glob("metadata.json"),
                      subdir.glob("*.zip"),
                      subdir.glob("*.zst")):
        if item.is_dir():
            item.rmdir()
        else:
            item.unlink()

for plat in debian_archs:
    subdir = here/("debian_" + plat)
    subdir.mkdir()
    subdir.cleardir()

    download_url = (f"{debian_pkg_url}/{PKG_NAME}-{DEB_SO_NO}-{DEB_SO_BUILD_NO}_"
                    f"{DEB_VERSION}-{DEB_BUILD_NO}_{plat}.deb")

    debian_pkg = subdir/f"{PKG_NAME}.deb"
    debian_pkg.write_bytes(requests.get(download_url, stream=True).content)

    patoolib.extract_archive(str(debian_pkg), outdir=str(subdir), verbosity=-1,
                             interactive=False)
    data_tar = subdir/"data.tar"
    data_tar.unpack_archive(subdir, format="zstdtar")

    debian_pkg.unlink()
    data_tar.unlink()
    for item in chain(subdir.glob("*.deb")):
        if item.is_dir():
            item.rmdir()
        else:
            item.unlink()
