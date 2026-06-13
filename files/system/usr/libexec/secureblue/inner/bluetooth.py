#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
The sandboxed bluetooth toggle function
"""

import os
import sys
from typing import Final

from utils import SystemdService

BLUE_MOD_FILE: Final[str] = "/etc/modprobe.d/99-bluetooth.conf"
BLUE_MOD_TEXT: Final[str] = """install bluetooth /sbin/modprobe --ignore-install bluetooth
install btusb /sbin/modprobe --ignore-install btusb
"""


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
                fd.write(BLUE_MOD_TEXT)
            os.chmod(BLUE_MOD_FILE, 0o644)
            bluetooth_service.unmask()
            bluetooth_service.enable_now()
            print("Bluetooth has been enabled. Reboot for effect.")
            return 0
        case "off":
            os.remove(BLUE_MOD_FILE)
            bluetooth_service.disable_now()
            bluetooth_service.mask()
            print("Bluetooth has been disabled. Reboot for effect.")
            return 0
        case _:
            print("Invalid inner script argument.")
            return 1


if __name__ == "__main__":
    sys.exit(main())
