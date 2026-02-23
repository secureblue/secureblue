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
from utils import CommandUsageError, ToggleMode, parse_basic_toggle_args

HOSTNAME_SENDING_HELP: Final[str] = """
This python script toggles if the system's hostname is sent to the DHCP server
by creating or deleting a configuration file at /etc/NetworkManager/conf.d/dhcp_no_hostname.conf"
to disable or enable this functionality.

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
    return not Path(HOSTNAME_SENDING_FILE).exists()


def print_status() -> None:
    """Print the current file status"""

    cur_status = "enabled" if hostname_sending_enabled() else "disabled"

    print(
        f"DHCP hostname sending is currently {cur_status}",
    )


def run(mode: ToggleMode) -> int:
    """Run the logic for enabling or disabling DHCP hostname sending"""

    disabled_by_file = Path(HOSTNAME_SENDING_FILE).exists()
    target_state_disabled = mode == ToggleMode.OFF
    state_already_set = target_state_disabled == disabled_by_file
    hostname_sending_function = sandbox.SandboxedFunction(
        "dhcp_hostname_sending.py", read_write_paths=[HOSTNAME_SENDING_DIR]
    )

    if mode == ToggleMode.HELP:
        print(HOSTNAME_SENDING_HELP)
        return 0
    enabled = hostname_sending_enabled()
    match mode:
        case ToggleMode.STATUS:
            print("enabled" if enabled else "disabled")
            return 0
        case ToggleMode.ON | ToggleMode.OFF:
            if state_already_set:
                print_status()
                return 0
            return sandbox.run(hostname_sending_function, mode)
        case _:
            raise ValueError(f"Invalid mode value: {mode}")


def main() -> int:
    """Handle the arguments and execute the toggle"""
    try:
        mode = parse_basic_toggle_args(
            prompt="Would you like to send the system's hostname to the DHCP server?"
        )
    except CommandUsageError as e:
        print(f"Usage error: {e}. see usage with --help.")
        return 2

    return run(mode)


if __name__ == "__main__":
    sys.exit(main())
