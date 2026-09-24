#!/usr/bin/python3

"""Sets kargs by loading/unloading UKI addons. Should be run as root."""

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from shared.kargs_hardening import (
    deserialize,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

LOADED_ADDONS_PATH = Path("/boot/loader/addons/")
AVAIL_ADDONS_PATH = Path("/usr/share/secureblue/uki/addons/")
ADDON_SUFFIX = ".addon.efi"


def karg_from_addon(addon: str) -> str:
    """Gets the karg from an addon filename.
    Raises:
        ValueError: Unexpected format of addon filename.
    """

    if not addon.endswith(ADDON_SUFFIX):
        raise ValueError(f"Filename must end with {ADDON_SUFFIX}.")

    karg = addon.replace("__", "=")
    return karg.removesuffix(ADDON_SUFFIX)


def addon_from_karg(karg: str) -> str:
    """Gets the addon filename from a karg."""

    addon = karg.replace("=", "__")
    return addon + ADDON_SUFFIX


def add_kargs(kargs: Sequence[str]) -> None:
    """Adds kargs by loading UKI addons."""

    LOADED_ADDONS_PATH.mkdir(exist_ok=True)

    addons = [addon_from_karg(karg) for karg in kargs]
    for addon in addons:
        (AVAIL_ADDONS_PATH / addon).copy_into(LOADED_ADDONS_PATH)


def remove_kargs(kargs: Sequence[str]) -> None:
    """Removes kargs by unloading UKI addons. Silently ignores kargs which don't exist."""

    addons = [addon_from_karg(karg) for karg in kargs]
    for addon in addons:
        (LOADED_ADDONS_PATH / addon).unlink(missing_ok=True)


def get_avail_kargs() -> set[str]:
    """Returns a set of all available kargs."""

    avail_kargs = [
        karg_from_addon(addon.name) for addon in AVAIL_ADDONS_PATH.glob("*" + ADDON_SUFFIX)
    ]
    return set(avail_kargs)


def get_loaded_kargs() -> set[str]:
    """Returns a set of the currently loaded kargs."""

    loaded_kargs = [
        karg_from_addon(addon.name) for addon in LOADED_ADDONS_PATH.glob("*" + ADDON_SUFFIX)
    ]
    return set(loaded_kargs)


def main() -> int:
    """Execute loading/unloading of UKI addons."""

    request = deserialize(sys.stdin.read())

    avail_kargs = get_avail_kargs()
    unavail_kargs = set(request.add) - avail_kargs
    if unavail_kargs:
        print(f"No addon available for the kargs: {', '.join(unavail_kargs)}")
        return 1

    add_kargs(request.add)
    remove_kargs(request.remove)

    loaded_kargs = get_loaded_kargs()

    kargs_not_loaded = set(request.add) - set(request.remove) - loaded_kargs
    if kargs_not_loaded:
        print(f"The following kargs couldn't be loaded: {', '.join(kargs_not_loaded)}")

    kargs_not_removed = set(request.remove) & loaded_kargs
    if kargs_not_removed:
        print(f"The following kargs couldn't be removed: {', '.join(kargs_not_removed)}")
        return 1

    # Deliberately done after kargs_not_removed so we get error messages for both.
    if kargs_not_loaded:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
