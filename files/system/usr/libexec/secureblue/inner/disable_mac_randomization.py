#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Disables MAC randomisation
"""

import os
import sys
from pathlib import Path

def disable_randomization() -> int:
    """Disables MAC address randomisation"""
    if Path("/etc/NetworkManager/conf.d/rand_mac.conf").exists():
        os.remove("/etc/NetworkManager/conf.d/rand_mac.conf")
    else:
        print(
            "MAC randomization config not found. This usually means MAC randomization was already off."
        )

    print("MAC randomization disabled")

    return 0




def main() -> int:
    """Main script entry point."""
    return disable_randomization()

if __name__ == "__main__":
    sys.exit(main())
