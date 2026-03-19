#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Disable brew."""

import os
import sys
from typing import Final

import sandbox
from utils import CommandUsageError, ToggleMode, parse_basic_toggle_args

BREW_HELP: Final[str] = """
This python script toggles if Homebrew is enabled by enabling or
disabling its tmpfiles.d configuration, removing or replacing the
brew.sh profile.d file, and removing the .linuxbrew directory.

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

BREW_TOGGLE_FUNCTION: Final[sandbox.SandboxedFunction] = sandbox.SandboxedFunction(
    "brew.py",
    read_write_paths=["/home/linuxbrew", "/etc/tmpfiles.d", "/etc/profile.d"],
    capabilities=["CAP_CHOWN", "CAP_DAC_OVERRIDE"],
)


def is_brew_installed() -> bool:
    """Test if Homebrew is installed."""
    return os.path.exists("/home/linuxbrew/.linuxbrew/bin/brew")


def print_status() -> None:
    """Print the current file and runtime status"""
    if is_brew_installed():
        print("Brew is enabled.")
    else:
        print("Brew is disabled.")


def enable_brew() -> int:
    """Enable Homebrew."""
    if is_brew_installed():
        print("Brew is already enabled.")
        return 0

    return sandbox.run(BREW_TOGGLE_FUNCTION, "on")


def disable_brew() -> int:
    """Disable Homebrew."""
    if not is_brew_installed():
        print("Brew is already disabled.")
        return 0

    return sandbox.run(BREW_TOGGLE_FUNCTION, "off")


def main() -> int:
    """Handle the arguments and execute the brew toggle"""
    try:
        mode = parse_basic_toggle_args(prompt="Would you like Homebrew to be enabled?")
    except CommandUsageError as e:
        print(f"Usage error: {e}. See usage with --help.")
        return 2

    match mode:
        case ToggleMode.ON:
            return enable_brew()
        case ToggleMode.OFF:
            return disable_brew()
        case ToggleMode.STATUS:
            print("Brew is enabled." if is_brew_installed() else "Brew is disabled.")
        case ToggleMode.HELP:
            print(BREW_HELP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
