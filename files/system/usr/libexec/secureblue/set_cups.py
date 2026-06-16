#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Enable or disable CUPS (the printing service)."""

import sys
from typing import Final, assert_never

import sandbox
from utils import CommandUsageError, ToggleMode, command_stdout, parse_basic_toggle_args

HELP_MESSAGE: Final[str] = """\
Enable or disable CUPS (the printing service).

Usage:
ujust set-cups
    Enables or disables interactively based on the user's preference.

ujust set-cups on
    Enables CUPS; does nothing if already on.

ujust set-cups off
    Disables CUPS; does nothing if already off.

ujust set-cups status
    Reports if CUPS is enabled or disabled.

ujust set-cups --help
    Prints this message.
"""


CUPS_FUNCTION = sandbox.SandboxedFunction(
    "cups.py",
    read_write_paths=["/etc/firewalld", "/etc/systemd/system"],
    remove_sandbox_arguments=["--property=InaccessiblePaths=/run/dbus/"],
)


def cups_status() -> str:
    return command_stdout("systemctl", "is-enabled", "cups.service", check=False)


def cups_print_status() -> int:
    if cups_status() == "enabled":
        print("CUPS (the printing service) is enabled.")
    else:
        print("CUPS (the printing service) is disabled.")
    return 0


def enable_cups() -> int:
    if cups_status() == "enabled":
        print("CUPS (the printing service) is already enabled.")
        return 0

    return sandbox.run(CUPS_FUNCTION, "on")


def disable_cups() -> int:
    if cups_status() == "masked":
        print("CUPS (the printing service) is already disabled.")
        return 0

    return sandbox.run(CUPS_FUNCTION, "off")


def main() -> int:
    try:
        mode = parse_basic_toggle_args(
            prompt="Would you like CUPS (the printing service) to be enabled?"
        )
    except CommandUsageError as e:
        print(f"Usage error: {e}. See usage with --help.")
        return 2

    match mode:
        case ToggleMode.ON:
            return enable_cups()
        case ToggleMode.OFF:
            return disable_cups()
        case ToggleMode.STATUS:
            return cups_print_status()
        case ToggleMode.HELP:
            print(HELP_MESSAGE)
        case _ as unreachable:
            assert_never(unreachable)
    return 0


if __name__ == "__main__":
    sys.exit(main())
