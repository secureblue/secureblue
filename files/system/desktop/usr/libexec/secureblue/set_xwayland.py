#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Enable or disable Xwayland."""

import os
import subprocess
import sys
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from files.system.usr.libexec.secureblue import utils
else:
    import utils

CommandUsageError: Final = utils.CommandUsageError
Image: Final = utils.Image
ToggleMode: Final = utils.ToggleMode
booted_image_ref: Final = utils.booted_image_ref
logout: Final = utils.logout
parse_basic_toggle_args: Final = utils.parse_basic_toggle_args

XWAYLAND_OVERRIDE_FILES: Final[dict[Image, str]] = {
    Image.SILVERBLUE: "/etc/systemd/user/org.gnome.Shell@user.service.d/override.conf",
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
    current_mode_enabled = not os.path.exists(override_file)
    new_mode = "disabled" if current_mode_enabled else "enabled"
    logout_prompt = (
        f"Xwayland for {de_name} has been {new_mode}. "
        "Would you like to log out now for this to take effect?"
    )

    match mode:
        case ToggleMode.STATUS:
            print("enabled" if current_mode_enabled else "disabled")
        case ToggleMode.ON:
            if current_mode_enabled:
                print(f"Xwayland for {de_name} is already enabled.")
            else:
                subprocess.run(
                    ["/usr/bin/run0", "/usr/bin/rm", "-f", "--", override_file], check=True
                )
                logout(prompt=logout_prompt)
        case ToggleMode.OFF:
            if current_mode_enabled:
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
                logout(prompt=logout_prompt)
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
