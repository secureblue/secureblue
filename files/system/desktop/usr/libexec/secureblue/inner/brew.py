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
import sys
from typing import Final

TMPFILES_OVERRIDE: Final[str] = "/etc/tmpfiles.d/homebrew.conf"
LINUXBREW_DIR: Final[str] = "/home/linuxbrew/.linuxbrew"
BREW_CACHE_DIR: Final[str] = "/home/linuxbrew/.cache"
BREW_PROFILE_FILE: Final[str] = "/etc/profile.d/brew.sh"
BREW_PROFILE_COMPLETIONS_FILE: Final[str] = "/etc/profile.d/brew-bash-completions.sh"
BREW_OWNER_UID: Final[int] = 1000


def _copy_and_chown(src: str, dst: str, *, follow_symlinks: bool = True) -> None:
    """Copy src to dest and chown the copy to the given UID."""
    shutil.copy2(src, dst, follow_symlinks=follow_symlinks)
    os.chown(dst, BREW_OWNER_UID, BREW_OWNER_UID, follow_symlinks=follow_symlinks)


def enable_brew() -> None:
    """Enable Homebrew."""
    with contextlib.suppress(FileNotFoundError):
        os.remove(TMPFILES_OVERRIDE)
    with contextlib.suppress(FileExistsError):
        shutil.copytree(
            "/usr/share/homebrew/.linuxbrew",
            LINUXBREW_DIR,
            symlinks=True,
            ignore_dangling_symlinks=True,
            copy_function=_copy_and_chown,
        )
    shutil.copy2(f"/usr{BREW_PROFILE_FILE}", BREW_PROFILE_FILE)
    shutil.copy2(f"/usr{BREW_PROFILE_COMPLETIONS_FILE}", BREW_PROFILE_COMPLETIONS_FILE)


def disable_brew() -> None:
    """Disable Homebrew."""
    with contextlib.suppress(FileExistsError):
        os.symlink("/dev/null", TMPFILES_OVERRIDE)
    with contextlib.suppress(FileNotFoundError):
        shutil.rmtree(LINUXBREW_DIR)
    with contextlib.suppress(FileNotFoundError):
        shutil.rmtree(BREW_CACHE_DIR)
    with contextlib.suppress(FileNotFoundError):
        os.remove(BREW_PROFILE_FILE)
    with contextlib.suppress(FileNotFoundError):
        os.remove(BREW_PROFILE_COMPLETIONS_FILE)


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
