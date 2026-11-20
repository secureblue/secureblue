#!/usr/bin/python3 -Es

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Enable, disable, or check status of SSH password authentication."""

import sys
from typing import Final, assert_never

import sandbox
from shared.ssh_password_auth import (
    SSH_AUTH_DROPIN,
    SSHD_CONFIG_DIR,
    SSHPasswordAuthError,
    ssh_password_auth_enabled,
)
from shared.utils import (
    CommandUsageError,
    ToggleMode,
    parse_basic_toggle_args,
    print_err,
    print_wrapped,
)

HELP_MESSAGE: Final[str] = """\
Toggles if SSH password authentication is allowed.

usage:
ujust set-ssh-password-auth
    Enables or disables interactively based on the user preference.

ujust set-ssh-password-auth on
    Removes the managed drop-in; does nothing if already on.
    Other SSH configuration disabling password authentication must be changed manually.

ujust set-ssh-password-auth off
    Disables SSH password authentication; does nothing if already off.

ujust set-ssh-password-auth status
    Reports if SSH password authentication is enabled or disabled in the effective configuration.

ujust set-ssh-password-auth --help
    Prints this message.
"""

ssh_auth_function = sandbox.SandboxedFunction(
    "ssh_password_auth.py",
    read_write_paths=[SSHD_CONFIG_DIR],
)


def enable_ssh_password_auth(currently_enabled: bool) -> int:
    """Enable SSH password authentication."""
    if currently_enabled:
        print("SSH password authentication is already enabled.")
        return 0
    print_wrapped(f"""
        SSH password authentication is currently disabled. Removing
        '{SSH_AUTH_DROPIN}' if present.
    """)
    print("Warning: reloading sshd.service may interrupt active SSH sessions.")
    exit_code = sandbox.run(ssh_auth_function, "on")
    if exit_code == 0:
        print("SSH password authentication enabled.")
    return exit_code


def disable_ssh_password_auth(currently_enabled: bool) -> int:
    """Disable SSH password authentication."""
    if not currently_enabled:
        print("SSH password authentication is already disabled.")
        return 0
    print_wrapped(f"""
        SSH password authentication is currently enabled. Disabling it now by creating
        '{SSH_AUTH_DROPIN}'.
    """)
    print("Warning: reloading sshd.service may interrupt active SSH sessions.")
    exit_code = sandbox.run(ssh_auth_function, "off")
    if exit_code == 0:
        print("SSH password authentication disabled.")
    return exit_code


def run(mode: ToggleMode) -> int:
    """Run the logic for enabling or disabling SSH password authentication."""
    if mode == ToggleMode.HELP:
        print(HELP_MESSAGE)
        return 0
    ssh_password_auth = ssh_password_auth_enabled()
    match mode:
        case ToggleMode.STATUS:
            print("enabled" if ssh_password_auth else "disabled")
            return 0
        case ToggleMode.ON:
            return enable_ssh_password_auth(ssh_password_auth)
        case ToggleMode.OFF:
            return disable_ssh_password_auth(ssh_password_auth)
        case _ as unreachable:
            assert_never(unreachable)


def main() -> int:
    """Handle the arguments and run the script."""
    try:
        mode = parse_basic_toggle_args(
            prompt="Would you like SSH password authentication to be enabled?"
        )
    except CommandUsageError as e:
        print(f"Usage error: {e}. See usage with --help.")
        return 2

    try:
        return run(mode)
    except SSHPasswordAuthError as error:
        print_err(str(error))
        return 1


if __name__ == "__main__":
    sys.exit(main())
