#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
The bluetooth toggle implementation for ujust
"""

import sys
from pathlib import Path
from typing import Final

import sandbox
from utils import (
    ask_yes_no,
    is_module_loaded,
)

BLUE_HELP: Final[str] = """
This python script toggles if bluetooth is enabled by creating or deleting a modprobe file at
"/etc/modprobe.d/99-bluetooth.conf" to disable or enable the kernel modules
needed for Bluetooth. Note this change only takes affect upon reboot.

usage:
ujust set-bluetooth-modules
    Turns Bluetooth on or off interactively based on the user's preference.

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


def print_status(enabled_by_file: bool) -> None:
    """Print the current file and runtime status"""

    bluetooth_currently_enabled = is_module_loaded("bluetooth") or is_module_loaded("btusb")
    file_matches_sys = "still " if enabled_by_file == bluetooth_currently_enabled else ""
    cur_status = "enabled" if bluetooth_currently_enabled else "disabled"
    file_status = "enabled" if enabled_by_file else "disabled"

    print(
        f"Bluetooth is currently {cur_status}, and after a reboot will",
        f"{file_matches_sys}be {file_status}",
    )


def main() -> int:
    """Handle the arguments and execute the bluetooth toggle"""

    argc_interactive = 1
    argc_on_off = 2

    if len(sys.argv) == argc_interactive:
        # Ask interactively.
        mode = "on" if ask_yes_no("Would you like to load the Bluetooth modules?") else "off"
    elif len(sys.argv) == argc_on_off:
        # Take mode from first argument, i.e. 'on' or 'off'.
        mode = sys.argv[1].casefold()
    else:
        print("Too many options specified, see usage with --help.", file=sys.stderr)
        return 1

    enabled_by_file = Path(BLUE_MOD_FILE).exists()
    bluetooth_function = sandbox.SandboxedFunction("bluetooth.py", read_write_paths=[BLUE_MOD_DIR])
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
