#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Enable or disable Gnome JIT JavaScript for GJS and WebkitGTK (requires session restart)."""

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final, assert_never

if TYPE_CHECKING:
    from files.system.usr.libexec.secureblue import sandbox, utils
else:
    import sandbox
    import utils

CommandUsageError: Final = utils.CommandUsageError
ToggleMode: Final = utils.ToggleMode
parse_basic_toggle_args: Final = utils.parse_basic_toggle_args
logout: Final = utils.logout


HELP_MESSAGE: Final[str] = """\
Enable or disable Gnome JIT JavaScript for GJS and WebkitGTK (requires session restart).

Usage:
ujust set-gnome-jit-js
    Enables or disables interactively based on the user's preference.

ujust set-gnome-jit-js on
    Enables Gnome JIT JS; does nothing if it is already on.

ujust set-gnome-jit-js off
    Disables Gnome JIT JS; does nothing if it is already off.

ujust set-gnome-jit-js status
    Reports whether Gnome JIT JS is enabled or disabled.

ujust set-gnome-jit-js --help
    Prints this message.
"""

GNOME_JIT_FUNCTION = sandbox.SandboxedFunction(
    "gnome_jit_js.py",
    read_write_paths=["/etc/profile.d"],
)


def gnome_jit_enabled() -> bool:
    return not Path("/etc/profile.d/gnome-disable-jit.sh").is_file()


def gnome_jit_status() -> None:
    if gnome_jit_enabled():
        print("Gnome JIT JS is enabled.")
    else:
        print("Gnome JIT JS is disabled.")


def enable_gnome_jit() -> None:
    if gnome_jit_enabled():
        print("Gnome JIT JS is already enabled.")
        return

    sandbox.run(GNOME_JIT_FUNCTION, "on")
    print("Gnome JIT JS has been enabled.")
    logout(prompt="Would you like to log out now for this to take effect?")


def disable_gnome_jit() -> None:
    if not gnome_jit_enabled():
        print("Gnome JIT JS is already disabled.")
        return

    sandbox.run(GNOME_JIT_FUNCTION, "off")
    print("Gnome JIT JS has been disabled.")
    logout(prompt="Would you like to log out now for this to take effect?")


def main() -> int:
    try:
        mode = parse_basic_toggle_args(prompt="Would you like Gnome JIT JS to be enabled?")
    except CommandUsageError as e:
        print(f"Usage error: {e}. See usage with --help.")
        return 2

    match mode:
        case ToggleMode.ON:
            enable_gnome_jit()
        case ToggleMode.OFF:
            disable_gnome_jit()
        case ToggleMode.STATUS:
            gnome_jit_status()
        case ToggleMode.HELP:
            print(HELP_MESSAGE)
        case _ as unreachable:
            assert_never(unreachable)
    return 0


if __name__ == "__main__":
    sys.exit(main())
