#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
The webcam toggle implementation for ujust
"""

import sys
from pathlib import Path
from typing import Final

import sandbox
from utils import (
    ask_yes_no,
    is_module_loaded,
)

WEBCAM_HELP: Final[str] = """
This python script toggles if webcam is enabled by creating or deleting a modprobe file at
"/etc/modprobe.d/99-disable-webcam.conf" to disable or enable the kernel modules
needed for webcam. Note this change only takes affect upon reboot.

usage:
ujust set-webcam-modules
    Turns Webcam on or off interactively based on the user's preference.

ujust set-webcam-modules on
    Turns Webcam on, does nothing if already on.

ujust set-webcam-modules off
    Turns Webcam off, does nothing if already off.

ujust set-webcam-modules status
    Reports if Webcam is set on or off.

ujust set-webcam-modules --help
    Prints this message.
"""

WEBCAM_MOD_DIR: Final[str] = "/etc/modprobe.d"
WEBCAM_MOD_FILE: Final[str] = f"{WEBCAM_MOD_DIR}/99-disable-webcam.conf"


def print_status(disabled_by_file: bool) -> None:
    """Print the current file and runtime status"""

    webcam_currently_enabled = is_module_loaded("uvcvideo")
    file_matches_sys = "still " if disabled_by_file == webcam_currently_enabled else ""
    cur_status = "enabled" if webcam_currently_enabled else "disabled"
    file_status = "disabled" if disabled_by_file else "enabled"

    print(
        f"Webcam is currently {cur_status}, and after a reboot will",
        f"{file_matches_sys}be {file_status}",
    )


def main() -> int:
    """Handle the arguments and execute the webcam toggle"""

    argc_interactive = 1
    argc_on_off = 2

    if len(sys.argv) == argc_interactive:
        # Ask interactively.
        mode = "on" if ask_yes_no("Would you like to load the Webcam modules?") else "off"
    elif len(sys.argv) == argc_on_off:
        # Take mode from first argument, i.e. 'on' or 'off'.
        mode = sys.argv[1].casefold()
    else:
        print("Too many options specified, see usage with --help.", file=sys.stderr)
        return 1

    disabled_by_file = Path(WEBCAM_MOD_FILE).exists()
    webcam_function = sandbox.SandboxedFunction("webcam.py", read_write_paths=[WEBCAM_MOD_DIR])
    match mode:
        case "on" | "off":
            target_state_enabled = mode == "on"
            state_already_set = target_state_enabled != disabled_by_file
            if state_already_set:
                print_status(disabled_by_file)
            else:
                return sandbox.run(webcam_function, mode)
        case "status":
            print_status(disabled_by_file)
        case "--help":
            print(WEBCAM_HELP)
        case _:
            print("Invalid option selected. Try --help.")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
