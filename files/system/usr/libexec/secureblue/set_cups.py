#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Enable or disable CUPS."""

from typing import Final
import sandbox
import sys

import utils

CommandUsageError: Final = utils.CommandUsageError
ToggleMode: Final = utils.ToggleMode
parse_basic_toggle_args: Final = utils.parse_basic_toggle_args
command_stdout: Final = utils.command_stdout

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
        "cups.py", read_write_paths=["/etc/firewalld", "/etc/systemd/system"]
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
            if cups_status != "masked":
                return sandbox.run(cups_function, "off")
            else:
                print("CUPS is already disabled.")

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
