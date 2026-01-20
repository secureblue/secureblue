#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Add Nvidia-specific kernel arguments."""

import sys

from kargs_hardening_common import IMAGE_NVIDIA_KARGS, apply_kargs


def main() -> int:
    """Main entry point for script."""
    if IMAGE_NVIDIA_KARGS is None:
        print("Error: not on a Nvidia image.")
        return 1
    print("Applying Nvidia-specific kernel arguments...")
    apply_kargs(add=IMAGE_NVIDIA_KARGS, remove=[])
    return 0


if __name__ == "__main__":
    sys.exit(main())
