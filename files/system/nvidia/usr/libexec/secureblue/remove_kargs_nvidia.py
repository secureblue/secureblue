#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Remove Nvidia-specific kernel arguments."""

import sys
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from files.system.usr.libexec.secureblue import kargs_hardening_common
else:
    import kargs_hardening_common

IMAGE_NVIDIA_KARGS: Final = kargs_hardening_common.IMAGE_NVIDIA_KARGS
apply_kargs: Final = kargs_hardening_common.apply_kargs


def main() -> int:
    """Main entry point for script."""
    if IMAGE_NVIDIA_KARGS is None:
        print("Error: not on a Nvidia image.")
        return 1
    print("Removing Nvidia-specific kernel arguments...")
    apply_kargs(add=[], remove=IMAGE_NVIDIA_KARGS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
