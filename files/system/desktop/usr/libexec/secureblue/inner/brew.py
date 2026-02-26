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

LINUXBREW_DIR: Final[str] = "/home/linuxbrew/.linuxbrew/"
BREW_ETC_STAMP: Final[str] = "/etc/.linuxbrew"
BREW_PROFILE_FILE: Final[str] = "/etc/profile.d/brew.sh"
BREW_PROFILE_COMPLETIONS_FILE: Final[str] = "/etc/profile.d/brew-bash-completions.sh"


def main() -> int:
    """Enable or disable brew"""

    required_args_count = 2
    if len(sys.argv) != required_args_count:
        return 1

    mode = sys.argv[1]
    match mode:
        case "on":
            subprocess.run(
                ["/usr/bin/systemctl", "enable", "--now", "brew-setup.service"],
                check=False,
                capture_output=True,
            )
            shutil.copy(f"/usr{BREW_PROFILE_FILE}", BREW_PROFILE_FILE)
            shutil.copy(f"/usr{BREW_PROFILE_COMPLETIONS_FILE}", BREW_PROFILE_COMPLETIONS_FILE)
            print("Brew is now enabled. Start a new shell to use brew.")
            return 0
        case "off":
            with contextlib.suppress(OSError):
                shutil.rmtree(LINUXBREW_DIR, ignore_errors=False)
            with contextlib.suppress(OSError):
                os.remove(BREW_ETC_STAMP)
            with contextlib.suppress(OSError):
                os.remove(BREW_PROFILE_FILE)
            with contextlib.suppress(OSError):
                os.remove(BREW_PROFILE_COMPLETIONS_FILE)
            subprocess.run(
                ["/usr/bin/systemctl", "disable", "brew-setup.service"],
                check=False,
                capture_output=True,
            )
            return 0
        case _:
            print("Invalid inner script argument.")
            return 1


if __name__ == "__main__":
    sys.exit(main())
