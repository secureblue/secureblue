#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Enable, disable, or check status of always-upgrade-on-boot."""

import sys
from pathlib import Path
from typing import Final

import sandbox
from utils import (
    CommandUsageError,
    ToggleMode,
    parse_basic_toggle_args,
    print_wrapped,
)

HELP_MESSAGE: Final[str] = """\
Toggles if always-upgrade-on-boot is allowed.

usage:
ujust set-always-upgrade-on-boot
    Enables or disables interactively based on the user's preference.

ujust set-always-upgrade-on-boot on
    Enables always-upgrade-on-boot; does nothing if already on.

ujust set-always-upgrade-on-boot off
    Disables always-upgrade-on-boot; does nothing if already off.

ujust set-always-upgrade-on-boot status
    Reports if always-upgrade-on-boot is enabled or disabled.

ujust set-always-upgrade-on-boot --help
    Prints this message.
"""

ALWAYS_UPGRADE_ON_BOOT_STAMPFILE: Final[str] = "/var/lib/secureblue/always-upgrade-on-boot.stamp"


def always_upgrade_on_boot_enabled() -> bool:
    """Return whether always-upgrade-on-boot is enabled."""
    return Path(ALWAYS_UPGRADE_ON_BOOT_STAMPFILE).exists()


stampfile_function = sandbox.SandboxedFunction(
    "set_stampfile.py",
    read_write_paths=["/var/lib/secureblue"],
)


def enable_always_upgrade_on_boot(currently_enabled: bool) -> int:
    """Enable always-upgrade-on-boot."""
    if currently_enabled:
        print("always-upgrade-on-boot is already enabled.")
        return 0
    print_wrapped(f"""
        always-upgrade-on-boot is currently disabled.
        Enabling it now by creating file '{ALWAYS_UPGRADE_ON_BOOT_STAMPFILE}'.
    """)
    exit_code = sandbox.run(stampfile_function, "create", ALWAYS_UPGRADE_ON_BOOT_STAMPFILE)
    if exit_code == 0:
        print("always-upgrade-on-boot enabled.")
    return exit_code


def disable_always_upgrade_on_boot(currently_enabled: bool) -> int:
    """Disable always-upgrade-on-boot."""
    if not currently_enabled:
        print("always-upgrade-on-boot is already disabled.")
        return 0
    print_wrapped(f"""
        always-upgrade-on-boot is currently enabled.
        Disabling it now by deleting file '{ALWAYS_UPGRADE_ON_BOOT_STAMPFILE}'.
    """)
    exit_code = sandbox.run(stampfile_function, "delete", ALWAYS_UPGRADE_ON_BOOT_STAMPFILE)
    if exit_code == 0:
        print("always-upgrade-on-boot disabled.")
    return exit_code


def run(mode: ToggleMode) -> int:
    """Run the logic for enabling or disabling always-upgrade-on-boot."""
    if mode == ToggleMode.HELP:
        print(HELP_MESSAGE)
        return 0
    auob_enabled = always_upgrade_on_boot_enabled()
    match mode:
        case ToggleMode.STATUS:
            print("enabled" if auob_enabled else "disabled")
            return 0
        case ToggleMode.ON:
            return enable_always_upgrade_on_boot(auob_enabled)
        case ToggleMode.OFF:
            return disable_always_upgrade_on_boot(auob_enabled)
        case _:
            raise ValueError(f"Invalid mode value: {mode}")


def main() -> int:
    """Handle the arguments and run the script."""
    try:
        mode = parse_basic_toggle_args(
            prompt="Would you like always-upgrade-on-boot to be enabled?"
        )
    except CommandUsageError as e:
        print(f"Usage error: {e}. See usage with --help.")
        return 2

    return run(mode)


if __name__ == "__main__":
    sys.exit(main())
