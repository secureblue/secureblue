#!/usr/bin/python3 -Es

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""The sandboxed SSH password authentication toggle function."""

import stat
import subprocess
import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Iterator

from shared.ssh_password_auth import (
    SSH_AUTH_DROPIN,
    SSH_AUTH_DROPIN_TEXT,
    SSHPasswordAuthError,
    SSHPasswordAuthStatus,
    read_ssh_password_auth_status,
)
from shared.utils import SystemdService, print_err

SSHD_SERVICE: Final[SystemdService] = SystemdService("sshd.service")


@contextmanager
def restore_dropin_on_error() -> Iterator[None]:
    """Restore the managed drop-in if changing or validating it fails."""
    try:
        contents = SSH_AUTH_DROPIN.read_bytes()
        mode = stat.S_IMODE(SSH_AUTH_DROPIN.stat().st_mode)
    except FileNotFoundError:
        contents = None
        mode = 0o644

    try:
        yield
    except (OSError, subprocess.CalledProcessError, SSHPasswordAuthError) as error:
        try:
            if contents is None:
                SSH_AUTH_DROPIN.unlink(missing_ok=True)
            else:
                with SSH_AUTH_DROPIN.open("wb") as dropin:
                    SSH_AUTH_DROPIN.chmod(mode)
                    dropin.write(contents)
        except OSError as restore_error:
            raise SSHPasswordAuthError(
                f"{error}\nUnable to restore {SSH_AUTH_DROPIN}: {restore_error}. "
                "Restore the configuration manually before restarting sshd."
            ) from restore_error
        raise


def reload_sshd() -> None:
    """Reload sshd if it is currently active."""
    if not SSHD_SERVICE.is_active():
        return

    SSHD_SERVICE.reload()


def disable_password_auth() -> None:
    """Disable SSH password authentication."""
    with restore_dropin_on_error():
        SSH_AUTH_DROPIN.parent.mkdir(parents=True, exist_ok=True)
        SSH_AUTH_DROPIN.parent.chmod(0o755)
        SSH_AUTH_DROPIN.write_text(SSH_AUTH_DROPIN_TEXT, encoding="utf-8")
        SSH_AUTH_DROPIN.chmod(0o644)
        if read_ssh_password_auth_status() != SSHPasswordAuthStatus.DISABLED:
            raise SSHPasswordAuthError(
                "SSH password authentication is still enabled despite the managed drop-in. "
                "Review /etc/ssh/sshd_config and /etc/ssh/sshd_config.d/ for settings that take precedence."
            )
    print("SSH password authentication has been disabled. Reloading sshd if active.")
    reload_sshd()


def enable_password_auth() -> None:
    """Enable SSH password authentication."""
    with restore_dropin_on_error():
        SSH_AUTH_DROPIN.unlink(missing_ok=True)
        if read_ssh_password_auth_status() != SSHPasswordAuthStatus.ENABLED:
            raise SSHPasswordAuthError(
                "SSH password authentication remains disabled by configuration outside the managed "
                "drop-in. Update /etc/ssh/sshd_config or /etc/ssh/sshd_config.d/ manually, "
                "then run this command again."
            )
    print("SSH password authentication has been enabled. Reloading sshd if active.")
    reload_sshd()


def main() -> int:
    """Read SSH configuration or set or remove the SSH password authentication drop-in."""
    if len(sys.argv[1:]) != 1:
        return 1

    mode = sys.argv[1]
    try:
        match mode:
            case "status":
                return read_ssh_password_auth_status()
            case "off":
                disable_password_auth()
            case "on":
                enable_password_auth()
            case _:
                print("Invalid inner script argument.")
                return 1
    except (OSError, subprocess.CalledProcessError, SSHPasswordAuthError) as error:
        print_err(str(error))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
