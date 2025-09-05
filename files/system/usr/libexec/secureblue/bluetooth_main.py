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
from sandbox import SandboxedFunction

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
BLUE_MOD_DIR: Final[str] = "/etc/modprobe.d"
BLUE_MOD_FILE: Final[str] = f"{BLUE_MOD_DIR}/99-bluetooth.conf"

class Bluetooth(SandboxedFunction):
    def __init__(self):
        super().__init__("CAP_DAC_OVERRIDE", [BLUE_MOD_DIR]) 

def is_module_loaded(module_name: str) -> bool:
    """Checks if a given kernel module is currently loaded by checking for it in /proc/modules"""
    try:
        with open("/proc/modules", encoding="utf8") as fd:
            return any(line.startswith(module_name + " ") for line in fd)
    except OSError:
        return False


def status(disabled_by_file: bool):
    """Gives status of Bluetooth availability, both currently and what it will be after a reboot."""
    bluetooth_currently_disabled: bool = not is_module_loaded("bluetooth") and not is_module_loaded("btusb")
    file_state_matches_system_string: str = "still " if disabled_by_file == bluetooth_currently_disabled else ""
    current_status_string: str = "disabled" if bluetooth_currently_disabled else "enabled"
    file_status_string: str = "disabled" if disabled_by_file else "enabled"

    print(f"Bluetooth is currently {current_status_string}, and after a reboot will {file_state_matches_system_string}be {file_status_string}")

def main():
    """Parses user input, checks current bluetooth status, and calls necessary helper functions."""
    disabled_by_file: bool = Path(
        BLUE_MOD_FILE
    ).exists()  # If this file exists, we assume the Bluetooth kernel modules are already disabled.
    if len(sys.argv) != 2:
        print("Needs an option, see usage with --help.")
        return 1

    mode = sys.argv[1]

    bluetooth_function = Bluetooth()
    match mode:
        case "on" | "off":
            target_state_disabled: bool = True if mode == "off" else False 
            state_already_set = target_state_disabled == disabled_by_file
            if (state_already_set):
                status(disabled_by_file)
            else:
                return sandbox.run(bluetooth_function, mode)
        case "status":
            status(disabled_by_file)
        case "--help":
            print(BLUE_HELP)
        case _:
            print("Invalid option selected. Try --help.")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
