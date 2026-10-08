""" """
import sys
if sys.version_info < (3,14):
    raise AssertionError("Python version 3.14 or higher is required.")
from utlx import module_path, Path

# https://anaconda.org/conda-forge/libusb/files/manage?channel=main&type=conda&version=1.0.30
# http://ftp.debian.org/debian/pool/main/libu/libusb-1.0/?C=M;O=D

here = Path(module_path())

PKG_NAME = "libusb"

CONDA_VERSION  = "1.0.30"
CONDA_BUILD_NO = "0"

DEB_PKG_SUBDIR   = "libu/libusb-1.0"
DEB_PKG_SUFFIX   = "-1.0"
DEB_BUILD_SUFFIX = "-0"
DEB_VERSION      = "1.0.30"
DEB_BUILD_NO     = "1"

conda_platforms = (
    # "win-64",
    # "win-arm64",
    # "linux-64",
    # "linux-aarch64",
    # "linux-ppc64le",
    "osx-64",
    "osx-arm64",
)

debian_archs = (
    "amd64",
    "i386",
    "arm64",
    "armhf",
    "ppc64el",
    "riscv64",
    "s390x",
    # "loong64",
)

def main(argv=sys.argv[1:]):
    download_conda_packages(PKG_NAME, CONDA_VERSION, conda_platforms, CONDA_BUILD_NO)
    download_debian_packages(PKG_NAME, DEB_VERSION, DEB_PKG_SUBDIR, debian_archs,
                             DEB_PKG_SUFFIX, DEB_BUILD_SUFFIX, DEB_BUILD_NO)
    download_debian_packages(PKG_NAME, "1.0.28", DEB_PKG_SUBDIR, ["armel"],
                             DEB_PKG_SUFFIX, DEB_BUILD_SUFFIX, "1")
    download_debian_packages(PKG_NAME, "1.0.26", DEB_PKG_SUBDIR, ["mips64el", "mipsel"],
                             DEB_PKG_SUFFIX, DEB_BUILD_SUFFIX, "1")
    return 0

def download_conda_packages(PKG_NAME, PKG_VERSION, conda_platforms, CONDA_BUILD_NO,
                            *, conda_channel="main", conda_type="conda",
                            conda_forge_url="https://anaconda.org/conda-forge"):
    import re
    from itertools import chain
    from urllib.parse import urlparse
    import requests
    import bs4
    from utlx import module_path, Path

    here = Path(module_path())

    conda_pkg_url = (f"{conda_forge_url}/{PKG_NAME}/files/manage?"
                     f"channel={conda_channel}&type={conda_type}&version={PKG_VERSION}")
    conda_main_url = "{}://{}".format(*urlparse(conda_pkg_url))

    html = requests.get(conda_pkg_url, stream=True).text
    soup = bs4.BeautifulSoup(html, "html.parser")

    for plat in conda_platforms:
        subdir = here/plat
        subdir.mkdir()
        subdir.cleartree()

        pattern = re.compile(rf"{plat}/{PKG_NAME}-{PKG_VERSION}-.+_{CONDA_BUILD_NO}\.conda")
        tag = soup.find("a", string=pattern)
        download_url = conda_main_url + tag["href"]

        conda_pkg = subdir/f"{PKG_NAME}.conda"
        conda_pkg.write_bytes(requests.get(download_url, stream=True).content)

        conda_pkg.unpack_archive(subdir, format="zip")

        for zstd in subdir.glob("*.zst"):
            zstd.unpack_archive(subdir, format="zstdtar")

        conda_pkg.unlink()
        for item in chain(subdir.glob("*.conda"),
                          subdir.glob("metadata.json"),
                          subdir.glob("*.zip"),
                          subdir.glob("*.zst")):
            if item.is_dir():
                item.rmtree()
            else:
                item.unlink()

def download_debian_packages(PKG_NAME, PKG_VERSION, DEB_PKG_SUBDIR, debian_archs,
                             DEB_PKG_SUFFIX, DEB_BUILD_SUFFIX, DEB_BUILD_NO,
                             *, debian_main_url="http://ftp.debian.org/debian/pool/main"):

    from itertools import chain
    import requests
    from utlx import module_path, Path
    import patoolib  # patool >= 4.0.5

    here = Path(module_path())

    debian_pkg_url = f"{debian_main_url}/{DEB_PKG_SUBDIR}"

    for plat in debian_archs:
        subdir = here/("debian_" + plat)
        subdir.mkdir()
        subdir.cleartree()

        download_url = (f"{debian_pkg_url}/{PKG_NAME}{DEB_PKG_SUFFIX}{DEB_BUILD_SUFFIX}_"
                        f"{PKG_VERSION}-{DEB_BUILD_NO}_{plat}.deb")

        debian_pkg = subdir/f"{PKG_NAME}.deb"
        debian_pkg.write_bytes(requests.get(download_url, stream=True).content)

        patoolib.extract_archive(str(debian_pkg), outdir=str(subdir), interactive=False,
                                 verbosity=-1)
        data_tar = subdir/"data.tar"
        data_tar.unpack_archive(subdir, format="zstdtar")

        debian_pkg.unlink()
        data_tar.unlink()
        for item in chain(subdir.glob("*.deb")):
            if item.is_dir():
                item.rmtree()
            else:
                item.unlink()


if __name__.rpartition(".")[-1] == "__main__":
    sys.exit(main())
