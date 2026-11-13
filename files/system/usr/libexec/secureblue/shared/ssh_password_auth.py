# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Shared SSH password authentication configuration and status checks."""

import subprocess
from enum import IntEnum
from pathlib import Path
from typing import Final

from .utils import command_stdout, parse_config

SSHD_CONFIG_DIR: Final[str] = "/etc/ssh/sshd_config.d"
SSH_AUTH_DROPIN: Final[Path] = Path(f"{SSHD_CONFIG_DIR}/49-secureblue-disable-password-auth.conf")
SSH_AUTH_DISABLED_CONFIG: Final[dict[str, str]] = {
    "PasswordAuthentication": "no",
    "KbdInteractiveAuthentication": "no",
}
SSH_AUTH_DROPIN_TEXT: Final[str] = "# This file is managed by secureblue.\n" + "".join(
    f"{key} {value}\n" for key, value in SSH_AUTH_DISABLED_CONFIG.items()
)


class SSHPasswordAuthError(Exception):
    """The effective SSH password authentication configuration could not be read or changed."""


class SSHPasswordAuthStatus(IntEnum):
    """Worker status codes, distinct from ordinary success and failure exit codes."""

    ENABLED = 10
    DISABLED = 11


def read_ssh_password_auth_status() -> SSHPasswordAuthStatus:
    """Read sshd's effective global settings. Must be called from the privileged worker."""
    try:
        output = command_stdout("/usr/sbin/sshd", "-T")
    except subprocess.CalledProcessError as error:
        details = (error.stderr or "").strip() or str(error)
        raise SSHPasswordAuthError(
            f"Unable to read the effective SSH configuration:\n{details}"
        ) from error

    config = parse_config(output.splitlines(), sep=" ")
    for key in SSH_AUTH_DISABLED_CONFIG:
        if config.get(key.casefold()) not in ("yes", "no"):
            raise SSHPasswordAuthError(
                f"Missing or invalid {key} in the effective SSH configuration."
            )

    if any(config[key.casefold()] != value for key, value in SSH_AUTH_DISABLED_CONFIG.items()):
        return SSHPasswordAuthStatus.ENABLED
    return SSHPasswordAuthStatus.DISABLED


def ssh_password_auth_enabled() -> bool:
    """Query SSH password authentication in a read-only privileged sandbox."""
    # The inner worker also imports this module, but does not import the sandbox launcher.
    import sandbox  # noqa: PLC0415

    try:
        exit_code = sandbox.SandboxedFunction("ssh_password_auth.py").run("status")
    except OSError as error:
        raise SSHPasswordAuthError("Unable to start the SSH configuration check.") from error

    match exit_code:
        case SSHPasswordAuthStatus.ENABLED:
            return True
        case SSHPasswordAuthStatus.DISABLED:
            return False
        case _:
            raise SSHPasswordAuthError(f"SSH configuration check failed (exit code {exit_code}).")
