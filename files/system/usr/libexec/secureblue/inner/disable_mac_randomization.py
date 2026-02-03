#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Disables MAC randomisation
"""

import os
import sys


def disable_randomization() -> int:
    """Disables MAC address randomisation"""
    try:
        os.remove("/etc/NetworkManager/conf.d/rand_mac.conf")
    except FileNotFoundError:
        return 1  # failure

    return 0  # success


def main() -> int:
    """Main script entry point."""
    return disable_randomization()


if __name__ == "__main__":
    sys.exit(main())
