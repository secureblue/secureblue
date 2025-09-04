"""
bluetooth_toggle.py

This module toggles bluetooth via modprobe rules.
"""

# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
from pathlib import Path
from typing import Final
import sandbox
from sandbox import Inner

BLUE_HELP: Final[str] = """
This python script toggles if bluetooth is enabled by creating or deleting a modprobe file at
"/etc/modprobe.d/99-bluetooth.conf" to disable or enable the kernel modules
needed for Bluetooth. Note this change only takes affect upon reboot.

usage:
ujust set-bluetooth-modules on
    Turns Bluetooth on, does nothing if already on.

ujust set-bluetooth-modules off
    Turns Bluetooth off, does nothing if already off.

ujust set-bluetooth-modules status
    Reports if Bluetooth is set on or off.

ujust set-bluetooth-modules --help
    Prints this message.
"""
# Note: If you are running this python script standalone use 'python3 bluetooth_toggle.py <option>'
BLUE_MOD_FILE: Final[str] = "/etc/modprobe.d/99-bluetooth.conf"


def is_module_loaded(module_name: str) -> bool:
    """Checks if a given kernel module is currently loaded by checking for it in /proc/modules"""
    try:
        with open("/proc/modules", encoding="utf8") as fd:
            return any(line.startswith(module_name + " ") for line in fd)
    except OSError:
        return False


def status(disabled: bool):
    """Gives status of Bluetooth availability, both currently and what it will be after a reboot."""
    message: str = ""
    if not is_module_loaded("bluetooth") and not is_module_loaded("btusb"):
        message += "Bluetooth is disabled currently"
    else:
        message += "Bluetooth is enabled currently"
    if disabled:
        message += ", and after a reboot, Bluetooth will be disabled."
    else:
        message += ", and after a reboot. Bluetooth will be enabled."
    print(message)


def main():
    """Parses user input, checks current bluetooth status, and calls necessary helper functions."""
    disabled: bool = Path(
        BLUE_MOD_FILE
    ).exists()  # If this file exists, we assume the Bluetooth kernel modules are already disabled.
    if len(sys.argv) != 2:
        print("Needs an option, see usage with --help.")
        return 1

    mode = sys.argv[1]
    match mode:
        case "on":
            if not disabled:
                status(disabled)
            else:
                return sandbox.run(Inner.BLUETOOTH, "CAP_DAC_OVERRIDE", "on")
        case "off":
            if disabled:
                status(disabled)
            else:
                return sandbox.run(Inner.BLUETOOTH, "CAP_DAC_OVERRIDE", "off")
        case "status":
            status(disabled)
        case "--help":
            print(BLUE_HELP)
        case _:
            print("Invalid option selected. Try --help.")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
