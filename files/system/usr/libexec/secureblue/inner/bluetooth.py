#!/usr/bin/python3 -Es

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
The sandboxed bluetooth toggle function
"""

import os
import subprocess
import sys
from typing import Final

from shared.utils import SystemdService

BLUE_KMODS: Final[list[str]] = ["bluetooth", "btusb"]
BLUE_MOD_FILE: Final[str] = "/etc/modprobe.d/99-bluetooth.conf"


def main() -> int:
    """Set or remove the bluetooth module override"""
    required_args_count = 2
    if len(sys.argv) != required_args_count:
        return 1
    bluetooth_service = SystemdService("bluetooth.service")
    mode = sys.argv[1]
    match mode:
        case "on":
            with open(BLUE_MOD_FILE, "w", encoding="utf8") as fd:
                fd.write(
                    "\n".join(
                        [
                            f"install {kmod} /sbin/modprobe --ignore-install {kmod}"
                            for kmod in BLUE_KMODS
                        ]
                    ) + "\n"
                )
            os.chmod(BLUE_MOD_FILE, 0o644)
            result = subprocess.run(["/usr/bin/modprobe", *BLUE_KMODS], check=False)
            if result.returncode != 0:
                print("Failed to load Bluetooth modules")
                return 1
            bluetooth_service.unmask()
            bluetooth_service.enable_now()
            print("Bluetooth has been enabled.")
            return 0
        case "off":
            os.remove(BLUE_MOD_FILE)
            bluetooth_service.disable_now()
            bluetooth_service.mask()
            result = subprocess.run(["/usr/bin/modprobe", *BLUE_KMODS], check=False)
            if result.returncode != 0:
                print("Failed to unload Bluetooth modules:", result.stderr)
                return 1
            print("Bluetooth has been disabled.")
            return 0
        case _:
            print("Invalid inner script argument.")
            return 1


if __name__ == "__main__":
    sys.exit(main())
