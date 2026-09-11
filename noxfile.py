# Copyright (c) 2026 Adam Karpierz
# SPDX-License-Identifier: Zlib

# /// script
# dependencies = ["nox>=2026.8.17", "nox_ext", "nox_lib"]
# ///

from __future__ import annotations

from typing import Any
import sys
import os
import shutil
import subprocess
import warnings

import nox
import nox_ext
import nox_lib
from nox_ext import print, pprint
from nox_lib.util import Path, copytree, rmtree

env = os.environ

# Configuration

PKG = nox.get_package_data()

PYPROJECT   = nox.project.load_toml("pyproject.toml")
PY_VERSIONS = nox.project.python_versions(PYPROJECT)
PY_DEFAULT  = "3.13"

# Prevent Python from writing bytecode
env["PYTHONDONTWRITEBYTECODE"] = "1"
# env["PKG_INITIAL_BUILD"] = "1"

# Sessions

@nox.session(python=[PY_DEFAULT], default=False,
    requires=["cleanup"])
def prepare(session: nox.Session) -> None:
    """Preparing the repository"""
    nox_lib.prepare.prep_cmd(session)

@nox.session(python=[PY_DEFAULT], default=False)
def cleanup(session: nox.Session) -> None:
    """Cleaning the repository"""
    nox_lib.cleanup.clean_cmd(session)
    nox_lib.cleanup.cleanup(session)

@nox.session(python=[*PY_VERSIONS, "pypy3.11"])
def tests(session: nox.Session) -> None:
    """Running tests"""
    session.install(".", "--group=test")
    nox_lib.tests.unittests(session)

@nox.session(python=[PY_DEFAULT], default=False)
def coverage(session: nox.Session) -> None:
    """Running code coverage analysis"""
    session.install(".", "--group=coverage")
    nox_lib.coverage.coverage(session)

@nox.session(python=[PY_DEFAULT])
def docs(session: nox.Session) -> None:
    """Building documentation and running doc tests"""
    session.install(".", "--group=docs")
    nox_lib.docs.sphinx(session)

@nox.session(python=[PY_DEFAULT], default=False,
    requires=["tests", "docs"])
def build(session: nox.Session) -> None:
    """Building the package"""
    session.install("--group=build")
    nox_lib.build.build(session, ignore_bad_ideas=["*.so"])

@nox.session(python=[PY_DEFAULT], default=False,
    requires=["build"])
def publish(session: nox.Session) -> None:
    """Publishing the package and documentation"""
    session.install("--group=publish")
    nox_lib.publish.on_pypi(session)
    nox_lib.publish.docs_on_gh_pages(session)

@nox.session(python=[PY_DEFAULT])
def typing(session: nox.Session) -> None:
    """Static type checking"""
    session.install(".", "--group=typing")
    nox_lib.typing.mypy(session)

@nox.session(python=[PY_DEFAULT])
def lint(session: nox.Session) -> None:
    """Checking code style and quality"""
    session.install(".", "--group=lint")
    nox_lib.lint.flake8(session)
