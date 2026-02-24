#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Enable or disable Xwayland."""

import os
import subprocess
import sys
from typing import Final

from utils import (
    CommandUsageError,
    Image,
    ToggleMode,
    booted_image_ref,
    parse_basic_toggle_args,
)

XWAYLAND_OVERRIDE_FILES: Final[dict[Image, str]] = {
    Image.SILVERBLUE: "/etc/systemd/user/org.gnome.Shell@wayland.service.d/override.conf",
    Image.KINOITE: "/etc/systemd/user/plasma-kwin_wayland.service.d/override.conf",
    Image.SERICEA: "/etc/sway/config.d/99-noxwayland.conf",
}

DE_NAMES: Final[dict[Image, str]] = {
    Image.SILVERBLUE: "GNOME",
    Image.KINOITE: "KDE Plasma",
    Image.SERICEA: "Sway",
}

HELP_MESSAGE: Final[str] = """\
Enable or disable Xwayland for the current desktop environment.

usage:
ujust set-xwayland
    Enables or disables interactively based on the user's preference.

ujust set-xwayland on
    Enables Xwayland; does nothing if already on.

ujust set-xwayland off
    Disables Xwayland; does nothing if already off.

ujust set-xwayland status
    Reports if Xwayland is enabled or disabled.

ujust set-xwayland --help
    Prints this message.
"""


def run(mode: ToggleMode) -> int:
    """Run script with a given mode."""
    mode = ToggleMode(mode)
    if mode == ToggleMode.HELP:
        print(HELP_MESSAGE)
        return 0

    image = Image.from_image_ref(booted_image_ref())
    if image not in XWAYLAND_OVERRIDE_FILES:
        print("The booted image does not support toggling Xwayland.")
        return 1

    override_file = XWAYLAND_OVERRIDE_FILES[image]
    de_name = DE_NAMES[image]
    enabled = not os.path.exists(override_file)

    match mode:
        case ToggleMode.STATUS:
            print("enabled" if enabled else "disabled")
        case ToggleMode.ON:
            if enabled:
                print(f"Xwayland for {de_name} is already enabled.")
            else:
                subprocess.run(
                    ["/usr/bin/run0", "/usr/bin/rm", "-f", "--", override_file], check=True
                )
                print(f"Xwayland for {de_name} has been enabled. Reboot to take effect.")
        case ToggleMode.OFF:
            if enabled:
                subprocess.run(
                    [
                        "/usr/bin/run0",
                        "/usr/bin/cp",
                        "-p",
                        "--",
                        f"/usr{override_file}",
                        override_file,
                    ],
                    check=True,
                )
                print(f"Xwayland for {de_name} has been disabled. Reboot to take effect.")
            else:
                print(f"Xwayland for {de_name} is already disabled.")

    return 0


def main() -> int:
    """Main script entry point."""
    try:
        mode = parse_basic_toggle_args(prompt="Would you like Xwayland to be enabled?")
    except CommandUsageError as e:
        print(f"Usage error: {e}. See usage with --help.")
        return 2
    return run(mode)


if __name__ == "__main__":
    sys.exit(main())
