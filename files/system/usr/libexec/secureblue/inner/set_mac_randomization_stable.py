#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Sets MAC randomization to per-network
"""

import os
import sys

CONFIG_STRING = """\
[device-mac-randomization]
wifi.scan-rand-mac-address=yes
[connection-mac-randomization]
ethernet.cloned-mac-address=stable
wifi.cloned-mac-address=stable
"""


def set_stable() -> int:
    """Sets MAC address randomisation to occur on a per-network basis."""

    with open("/etc/NetworkManager/conf.d/rand_mac.conf", "w", encoding="utf-8") as f:
        f.write(CONFIG_DOCSTRING)

    os.chmod("/etc/NetworkManager/conf.d/rand_mac.conf", 0o644)

    return 0


def main() -> int:
    """Main script entry point."""
    return set_stable()


if __name__ == "__main__":
    sys.exit(main())
