#!/usr/bin/python3

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

"""
The bluetooth toggle implementation for ujust
"""

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

BLUE_MOD_DIR: Final[str] = "/etc/modprobe.d"
BLUE_MOD_FILE: Final[str] = f"{BLUE_MOD_DIR}/99-bluetooth.conf"


def is_module_loaded(module_name: str) -> bool:
    """Check whether the passed module name is currently loaded"""

    try:
        with open("/proc/modules", encoding="utf8") as fd:
            return any(line.startswith(module_name + " ") for line in fd)
    except OSError:
        return False


def print_status(enabled_by_file: bool) -> None:
    """Print the current file and runtime status"""

    bluetooth_currently_enabled = is_module_loaded("bluetooth") or is_module_loaded("btusb")
    file_matches_sys = "still " if enabled_by_file == bluetooth_currently_enabled else ""
    cur_status = "enabled" if bluetooth_currently_enabled else "disabled"
    file_status = "enabled" if enabled_by_file else "disabled"

    print(
        f"Bluetooth is currently {cur_status}, and after a reboot will {file_matches_sys}be {file_status}"
    )


def main() -> int:
    """Handle the arguments and execute the bluetooth toggle"""

    enabled_by_file = Path(BLUE_MOD_FILE).exists()

    required_args_count = 2
    if len(sys.argv) != required_args_count:
        print("Needs an option, see usage with --help.")
        return 1

    mode = sys.argv[1]

    bluetooth_function = SandboxedFunction("bluetooth.py", read_write_paths=[BLUE_MOD_DIR])
    match mode:
        case "on" | "off":
            target_state_enabled = mode == "on"
            state_already_set = target_state_enabled == enabled_by_file
            if state_already_set:
                print_status(enabled_by_file)
            else:
                return sandbox.run(bluetooth_function, mode)
        case "status":
            print_status(enabled_by_file)
        case "--help":
            print(BLUE_HELP)
        case _:
            print("Invalid option selected. Try --help.")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
