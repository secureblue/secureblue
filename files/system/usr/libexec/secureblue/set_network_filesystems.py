#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Enable or disable support for network filesystems (NFS, CIFS)."""

import sys
from typing import Final, assert_never

import sandbox
from utils import CommandUsageError, ToggleMode, parse_basic_toggle_args

HELP_MESSAGE: Final[str] = """\
Enable or disable support for network filesystems (NFS, CIFS).

Usage:
ujust set-network-filesystem-modules
    Enables or disables interactively based on the user's preference.

ujust set-network-filesystem-modules on
    Enables network filesystems; does nothing if already on.

ujust set-network-filesystem-modules off
    Disables network filesystems; does nothing if already off.

ujust set-network-filesystem-modules status
    Reports if network filesystems is enabled or disabled.

ujust set-network-filesystem-modules --help
    Prints this message.
"""


NETFS_MODULE_DIR: Final[str] = "/etc/modprobe.d"
NETFS_MODULE_FILE: Final[str] = f"{NETFS_MODULE_DIR}/99-network-filesystems.conf"

NETFS_FUNCTION = sandbox.SandboxedFunction(
    "network_filesystems.py",
    read_write_paths=[NETFS_MODULE_DIR],
)


def network_filesystems_status() -> str:
    return "enabled" if Path(NETFS_MODULE_FILE).exists() else "disabled"


def network_filesystems_print_status() -> int:
    if network_filesystems_status() == "enabled":
        print("Network filesystems is enabled.")
    else:
        print("Network filesystems is disabled.")
    return 0


def enable_network_filesystems() -> int:
    if network_filesystems_status() == "enabled":
        print("Network filesystems is already enabled.")
        return 0

    return sandbox.run(NETFS_FUNCTION, "on")


def disable_network_filesystems() -> int:
    if network_filesystems_status() == "disabled":
        print("Network filesystems is already disabled.")
        return 0

    return sandbox.run(NETFS_FUNCTION, "off")


def main() -> int:
    try:
        mode = parse_basic_toggle_args(
            prompt="Would you like to enable network filesystems (NFS, CIFS)?"
        )
    except CommandUsageError as e:
        print(f"Usage error: {e}. See usage with --help.")
        return 2

    match mode:
        case ToggleMode.ON:
            return enable_network_filesystems()
        case ToggleMode.OFF:
            return disable_network_filesystems()
        case ToggleMode.STATUS:
            return network_filesystems_print_status()
        case ToggleMode.HELP:
            print(HELP_MESSAGE)
        case _ as unreachable:
            assert_never(unreachable)
    return 0


if __name__ == "__main__":
    sys.exit(main())
