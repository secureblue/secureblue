#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
The DHCP hostname sending toggle implementation for ujust
"""

import sys
from pathlib import Path
from typing import Final

import sandbox
from utils import ask_yes_no

HOSTNAME_SENDING_HELP: Final[str] = """
This python script toggles if the system's hostname is sent to the DHCP server by creating or deleting a configuration file at
"/etc/NetworkManager/conf.d/dhcp_no_hostname.conf" to disable or enable this functionality.

usage:
ujust set-dhcp-hostname-sending
    Enables or disables interactively based on the user's preference.

ujust set-dhcp-hostname-sending on
    Enables hostname sending to the DHCP server; does nothing if already on.

ujust set-dhcp-hostname-sending off
    Disables hostname sending to the DHCP server; does nothing if already off.

ujust set-dhcp-hostname-sending status
    Reports whether the system is set to send its hostname to the DHCP server or not.

ujust set-dhcp-hostname-sending --help
    Prints this message.
"""


HOSTNAME_SENDING_DIR: Final[str] = "/etc/NetworkManager/conf.d"
HOSTNAME_SENDING_FILE: Final[str] = f"{HOSTNAME_SENDING_DIR}/dhcp_no_hostname.conf"


def hostname_sending_enabled() -> bool:
    """Return whether the system is set to send its hostname to the DHCP server or not."""
    if Path(HOSTNAME_SENDING_FILE).exists():
        return False
    else:
        return True


def print_status(disabled_by_file: bool) -> None:
    """Print the current file and runtime status"""

    cur_status = "enabled" if hostname_sending_enabled() else "disabled"

    print(
        f"DHCP hostname sending is currently {cur_status}",
    )


def main() -> int:
    """Handle the arguments and execute the toggle"""

    argc_interactive = 1
    argc_on_off = 2

    if len(sys.argv) == argc_interactive:
        # Ask interactively.
        mode = "on" if ask_yes_no("Would you like to send the system's hostname to the DHCP server?") else "off"
    elif len(sys.argv) == argc_on_off:
        # Take mode from first argument, i.e. 'on' or 'off'.
        mode = sys.argv[1].casefold()
    else:
        print("Too many options specified, see usage with --help.", file=sys.stderr)
        return 1

    disabled_by_file = Path(HOSTNAME_SENDING_FILE).exists()
    hostname_sending_function = sandbox.SandboxedFunction("dhcp_hostname_sending.py", read_write_paths=[HOSTNAME_SENDING_DIR])
    match mode:
        case "on" | "off":
            target_state_disabled = mode == "off"
            state_already_set = target_state_disabled == disabled_by_file
            if state_already_set:
                print_status(disabled_by_file)
            else:
                return sandbox.run(hostname_sending_function, mode)
        case "status":
            print_status(disabled_by_file)
        case "--help":
            print(HOSTNAME_SENDING_HELP)
        case _:
            print("Invalid option selected. Try --help.")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
