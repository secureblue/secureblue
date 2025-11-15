#!/usr/bin/python3

# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Disable brew."""

import os
import shutil
import subprocess  # nosec
import sys
from pathlib import Path
from typing import Final

import sandbox
from sandbox import SandboxedFunction
from utils import ask_yes_no

BREW_HELP: Final[str] = """
This python script toggles if brew is enabled by enabling or disabling
brew-setup.service, removing or replacing the brew.sh profile.d file,
and removing the .linuxbrew directory.

usage:
ujust set-brew
    Enables or disables brew interactively based on the user's preference.

ujust set-brew on
    Enables brew, does nothing if already on.

ujust set-brew off
    Disables brew, does nothing if already off.

ujust set-brew status
    Reports if Brew is enabled or disabled.

ujust set-brew --help
    Prints this message.
"""


LINUXBREW_HOMEDIR: Final[str] = "/home/linuxbrew/"
ETC_DIR: Final[str] = "/etc"
BREW_ETC_STAMP: Final[str] = "/etc/.linuxbrew"


def print_status(linuxbrew_installed_by_stamp: bool) -> None:
    """Print the current file and runtime status"""

    # nosemgrep: dangerous-subprocess-use-audit
    brew_setup_status = subprocess.run(  # nosec
        ["/usr/bin/systemctl", "is-enabled", "--quiet", "brew-setup.service"],
        check=False,
        capture_output=True,
    )

    is_brew_setup_enabled = brew_setup_status.returncode == 0
    if linuxbrew_installed_by_stamp and is_brew_setup_enabled:
        print("Brew is enabled.")
    elif not linuxbrew_installed_by_stamp and not is_brew_setup_enabled:
        print("Brew is disabled.")
    elif not linuxbrew_installed_by_stamp and is_brew_setup_enabled:
        print("Brew has been locally modified. Brew is enabled but not installed.")
        print("Ensure state consistency between /etc/.linuxbrew and brew-setup.service.")
    else:
        print("Brew has been locally modified. Brew is installed but disabled.")
        print("Ensure state consistency between /etc/.linuxbrew and brew-setup.service.")


def main() -> None:
    """Handle the arguments and execute the brew toggle"""

    argc_interactive = 1
    argc_on_off = 2

    if len(sys.argv) == argc_interactive:
        # Ask interactively.
        mode = "on" if ask_yes_no("Would you like Homebrew to be enabled?") else "off"
    elif len(sys.argv) == argc_on_off:
        # Take mode from first argument, i.e. 'on' or 'off'.
        mode = sys.argv[1].casefold()
    else:
        print("Too many options specified, see usage with --help.", file=sys.stderr)
        return 1

    linuxbrew_is_installed = Path(BREW_ETC_STAMP).exists()
    brew_disable_function = SandboxedFunction(
        "brew.py", read_write_paths=[LINUXBREW_HOMEDIR, ETC_DIR], capabilities=["CAP_DAC_OVERRIDE"]
    )
    match mode:
        case "on" | "off":
            target_state_enabled = mode == "on"
            state_already_set = target_state_enabled == linuxbrew_is_installed
            if state_already_set:
                print_status(linuxbrew_is_installed)
            else:
                if not target_state_enabled:
                    brew_cache_dir = os.path.expanduser("~/.cache/Homebrew")
                    shutil.rmtree(brew_cache_dir, ignore_errors=True)
                return sandbox.run(brew_disable_function, mode)
        case "status":
            print_status(linuxbrew_is_installed)
        case "--help":
            print(BREW_HELP)
        case _:
            print("Invalid option selected. Try --help.")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
