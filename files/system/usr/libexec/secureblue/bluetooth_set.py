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

import sys
import os
from pathlib import Path
from typing import Final
from utils import sandbox

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

BLUE_MOD_PATH: Final[str] = "/etc/modprobe.d/"
BLUE_MOD_FILE: Final[str] = "/etc/modprobe.d/99-bluetooth.conf"
BLUE_MOD_TEXT: Final[str] = """install bluetooth /sbin/modprobe --ignore-install bluetooth
install btusb /sbin/modprobe --ignore-install btusb"""
RUN0_CONFIG: Final[list[str]] = [BLUE_MOD_FILE, "CAP_DAC_OVERRIDE"]


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


@sandbox(RUN0_CONFIG)
def inner(mode: bool):
    """Checks arguements, and adds or deletes the relevant modprobe file."""

    match mode:
        case 0:
            with open(BLUE_MOD_FILE, "w", encoding="utf8") as fd:
                fd.write(BLUE_MOD_TEXT)
            os.chmod(BLUE_MOD_FILE, 0o644)
            print("Bluetooth has been disabled. Reboot for effect.")
            return 0
        case 1:
            os.remove(BLUE_MOD_FILE)
            print("Bluetooth has been enabled. Reboot for effect.")
            return 0
        case _:
            print("Invalid inner script argument.")
            return 1


def main():
    """Parses user input, checks current bluetooth status, and calls necessary helper functions."""
    disabled: bool = Path(
        BLUE_MOD_FILE
    ).exists()  # If this file exists, we assume the Bluetooth kernel modules are already disabled.
    if len(sys.argv) == 1:
        print("Needs an option, see usage with --help.")
        return 1

    mode = sys.argv[1]
    match mode:
        case "on":
            if not disabled:
                status(disabled)
            else:
                return inner(True)
        case "off":
            if disabled:
                status(disabled)
            else:
                return inner(False)
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
