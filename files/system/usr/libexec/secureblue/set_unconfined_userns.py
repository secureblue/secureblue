#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Enable, disable, or check status of unconfined-domain user namespace creation."""

import subprocess  # nosec
import sys
from typing import Final

import sandbox
from utils import (
    CommandUsageError,
    ToggleMode,
    command_succeeds,
    parse_basic_toggle_args,
    print_wrapped,
)

HELP_MESSAGE: Final[str] = """\
Toggles if unconfined-domain user namespace creation is allowed.

usage:
ujust set-unconfined-userns
    Enables or disables interactively based on the user's preference.

ujust set-unconfined-userns on
    Enables unconfined-domain userns creation; does nothing if already on.

ujust set-unconfined-userns off
    Disables unconfined-domain userns creation; does nothing if already off.

ujust set-unconfined-userns status
    Reports if unconfined-domain userns creation is enabled or disabled.

ujust set-unconfined-userns --help
    Prints this message.
"""

UNCONFINED_USERNS_MODULE: Final[str] = "harden_userns"


def unconfined_userns_enabled() -> bool:
    """Return whether unconfined-domain user namespace creation is enabled."""
    # First try to read the list of enabled SELinux modules directly.
    semodule_proc = subprocess.run(
        ["/usr/bin/semodule", "-l"], check=False, capture_output=True, text=True
    )  # nosec
    if semodule_proc.returncode == 0:
        return UNCONFINED_USERNS_MODULE not in semodule_proc.stdout.splitlines()

    # If we can't run `semodule -l`, we're running unprivileged and therefore we check
    # whether `unshare -U true` succeeds, which lets us infer the state of the module.
    return command_succeeds("/usr/bin/unshare", "-U", "/usr/bin/true")


semodule_function = sandbox.SandboxedFunction(
    "set_selinux_module.py",
    read_write_paths=["/etc"],
    capabilities=["CAP_DAC_OVERRIDE"],
)


def enable_unconfined_userns(currently_enabled: bool) -> int:
    """Enable unconfined-domain user namespace creation."""
    if currently_enabled:
        print("Unconfined-domain user namespace creation is already enabled.")
        return 0
    print_wrapped(f"""
        Unconfined-domain user namespace creation (e.g. for bubblejail) is currently
        disabled. Enabling it now by disabling SELinux module '{UNCONFINED_USERNS_MODULE}'.
    """)
    exit_code = sandbox.run(semodule_function, "disable", UNCONFINED_USERNS_MODULE)
    if exit_code == 0:
        print("Unconfined-domain user namespace creation enabled.")
    return exit_code


def disable_unconfined_userns(currently_enabled: bool) -> int:
    """Disable unconfined-domain user namespace creation."""
    if not currently_enabled:
        print("Unconfined-domain user namespace creation is already disabled.")
        return 0
    print_wrapped(f"""
        Unconfined-domain user namespace creation (e.g. for bubblejail) is currently
        enabled. Disabling it now by enabling SELinux module '{UNCONFINED_USERNS_MODULE}'.
    """)
    exit_code = sandbox.run(semodule_function, "enable", UNCONFINED_USERNS_MODULE)
    if exit_code == 0:
        print("Unconfined-domain user namespace creation disabled.")
    return exit_code


def run(mode: ToggleMode) -> int:
    """Run the logic for enabling or disabling unconfined-domain userns."""
    if mode == ToggleMode.HELP:
        print(HELP_MESSAGE)
        return 0
    userns_enabled = unconfined_userns_enabled()
    match mode:
        case ToggleMode.STATUS:
            print("enabled" if userns_enabled else "disabled")
            return 0
        case ToggleMode.ON:
            return enable_unconfined_userns(userns_enabled)
        case ToggleMode.OFF:
            return disable_unconfined_userns(userns_enabled)


def main() -> int:
    """Handle the arguments and run the script."""
    try:
        mode = parse_basic_toggle_args(
            prompt="Would you like unconfined-domain user namespace creation to be enabled?"
        )
    except CommandUsageError as e:
        print(f"Usage error: {e}. See usage with --help.")
        return 2

    return run(mode)


if __name__ == "__main__":
    sys.exit(main())
