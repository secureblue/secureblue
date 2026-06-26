#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Enable, disable, or check status of SSH password authentication."""

import sys
from pathlib import Path
from typing import Final, assert_never

import sandbox
from utils import (
    CommandUsageError,
    ToggleMode,
    parse_basic_toggle_args,
    parse_config,
    print_wrapped,
)

HELP_MESSAGE: Final[str] = """\
Toggles if SSH password authentication is allowed.

usage:
ujust set-ssh-password-auth
    Enables or disables interactively based on the user preference.

ujust set-ssh-password-auth on
    Enables SSH password authentication; does nothing if already on.

ujust set-ssh-password-auth off
    Disables SSH password authentication; does nothing if already off.

ujust set-ssh-password-auth status
    Reports if SSH password authentication is enabled or disabled.

ujust set-ssh-password-auth --help
    Prints this message.
"""

SSHD_CONFIG_DIR: Final[str] = "/etc/ssh/sshd_config.d"
SSH_AUTH_DROPIN: Final[Path] = Path(f"{SSHD_CONFIG_DIR}/49-secureblue-disable-password-auth.conf")
SSH_AUTH_DISABLED_CONFIG: Final[dict[str, str]] = {
    "PasswordAuthentication": "no",
    "KbdInteractiveAuthentication": "no",
}


ssh_auth_function = sandbox.SandboxedFunction(
    "ssh_password_auth.py",
    read_write_paths=[SSHD_CONFIG_DIR],
)


def ssh_password_auth_enabled() -> bool:
    """Return whether SSH password authentication is enabled."""
    try:
        with SSH_AUTH_DROPIN.open(encoding="utf-8") as f:
            config = parse_config(f, sep=" ")
    except FileNotFoundError:
        return True

    return any(config.get(key) != value for key, value in SSH_AUTH_DISABLED_CONFIG.items())


def enable_ssh_password_auth(currently_enabled: bool) -> int:
    """Enable SSH password authentication."""
    if currently_enabled:
        print("SSH password authentication is already enabled.")
        return 0
    print_wrapped(f"""
        SSH password authentication is currently disabled. Enabling it now by removing
        '{SSH_AUTH_DROPIN}'.
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

    return run(mode)


if __name__ == "__main__":
    sys.exit(main())
