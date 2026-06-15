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
Enable or disable CUPS.

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


def run(mode: ToggleMode) -> int:
    mode = ToggleMode(mode)
    if mode == ToggleMode.HELP:
        print(HELP_MESSAGE)
        return 0

    cups_function = sandbox.SandboxedFunction(
        "cups.py",
        read_write_paths=["/etc/firewalld", "/etc/systemd/system"],
        remove_sandbox_arguments=["--property=InaccessiblePaths=/run/dbus/"],
    )
    cups_status = command_stdout("systemctl", "is-enabled", "cups.service", check=False)

    match mode:
        case ToggleMode.STATUS:
            print("Enabled" if cups_status == "enabled" else "Disabled")
        case ToggleMode.ON:
            if cups_status == "enabled":
                print("CUPS is already enabled.")
            else:
                return sandbox.run(cups_function, "on")
        case ToggleMode.OFF:
            if cups_status == "masked":
                print("CUPS is already disabled.")
            else:
                return sandbox.run(cups_function, "off")
        case _ as unreachable:
            assert_never(unreachable)

    return 0


def main() -> int:
    try:
        mode = parse_basic_toggle_args(prompt="Would you like CUPS to be enabled?")
    except CommandUsageError as e:
        print(f"Usage error: {e}. See usage with --help.")
        return 2
    return run(mode)


if __name__ == "__main__":
    sys.exit(main())
