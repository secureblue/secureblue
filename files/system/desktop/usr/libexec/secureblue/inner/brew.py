#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
The sandboxed brew disable function
"""

import contextlib
import os
import shutil
import subprocess
import sys
from typing import Final

LINUXBREW_HOME: Final[str] = "/home/linuxbrew"
TMPFILES_OVERRIDE: Final[str] = "/etc/tmpfiles.d/homebrew.conf"
BREW_PROFILE_FILE: Final[str] = "/etc/profile.d/brew.sh"
BREW_PROFILE_COMPLETIONS_FILE: Final[str] = "/etc/profile.d/brew-bash-completions.sh"
BREW_SYSTEMD_UNITS: Final[list[str]] = [
    "brew-update.service",
    "brew-update.timer",
    "brew-upgrade.service",
    "brew-upgrade.timer",
    "brew-proxy-daemon.service",
]


def enable_brew() -> None:
    """Enable Homebrew."""
    with contextlib.suppress(FileNotFoundError):
        os.remove(TMPFILES_OVERRIDE)
    subprocess.run(
        ["/usr/bin/systemd-tmpfiles", "--create", f"--prefix={LINUXBREW_HOME}"], check=True
    )
    shutil.copy2(f"/usr{BREW_PROFILE_FILE}", BREW_PROFILE_FILE)
    shutil.copy2(f"/usr{BREW_PROFILE_COMPLETIONS_FILE}", BREW_PROFILE_COMPLETIONS_FILE)
    subprocess.run(["/usr/bin/systemctl", "unmask", "--", *BREW_SYSTEMD_UNITS], check=True)


def disable_brew() -> None:
    """Disable Homebrew."""
    with contextlib.suppress(FileExistsError):
        os.symlink("/dev/null", TMPFILES_OVERRIDE)
    with contextlib.suppress(FileNotFoundError):
        os.chmod(LINUXBREW_HOME, 0o700)
    with contextlib.suppress(FileNotFoundError):
        os.remove(BREW_PROFILE_FILE)
    with contextlib.suppress(FileNotFoundError):
        os.remove(BREW_PROFILE_COMPLETIONS_FILE)
    subprocess.run(["/usr/bin/systemctl", "mask", "--now", "--", *BREW_SYSTEMD_UNITS], check=True)


def main() -> int:
    """Enable or disable brew"""

    required_args_count = 2
    if len(sys.argv) != required_args_count:
        return 1

    mode = sys.argv[1].casefold()
    match mode:
        case "on":
            enable_brew()
            print("Brew is now enabled. Start a new shell to use brew.")
            return 0
        case "off":
            disable_brew()
            print("Brew is now disabled.")
            return 0
        case _:
            print("Invalid inner script argument.")
            return 1


if __name__ == "__main__":
    sys.exit(main())
