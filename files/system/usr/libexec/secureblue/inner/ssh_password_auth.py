#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""The sandboxed SSH password authentication toggle function."""

import subprocess
import sys
from pathlib import Path
from typing import Final

SSH_AUTH_DROPIN: Final[Path] = Path(
    "/etc/ssh/sshd_config.d/49-secureblue-disable-password-auth.conf"
)
SSH_AUTH_DROPIN_TEXT: Final[str] = """# This file is managed by secureblue.
PasswordAuthentication no
KbdInteractiveAuthentication no
"""


def reload_sshd() -> int:
    """Reload sshd if it is currently active."""
    is_active = subprocess.run(
        ["/usr/bin/systemctl", "is-active", "--quiet", "sshd.service"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if is_active.returncode != 0:
        return 0

    systemctl = subprocess.run(
        ["/usr/bin/systemctl", "reload", "sshd.service"],
        check=False,
    )
    if systemctl.returncode != 0:
        print("Failed to reload sshd.service.", file=sys.stderr)
    return systemctl.returncode


def disable_password_auth() -> int:
    """Disable SSH password authentication."""
    SSH_AUTH_DROPIN.parent.mkdir(parents=True, exist_ok=True)
    SSH_AUTH_DROPIN.write_text(SSH_AUTH_DROPIN_TEXT, encoding="utf-8")
    SSH_AUTH_DROPIN.chmod(0o644)
    print("SSH password authentication has been disabled. Reloading sshd if active.")
    return reload_sshd()


def enable_password_auth() -> int:
    """Enable SSH password authentication."""
    SSH_AUTH_DROPIN.unlink(missing_ok=True)
    print("SSH password authentication has been enabled. Reloading sshd if active.")
    return reload_sshd()


def main() -> int:
    """Set or remove the SSH password authentication drop-in."""
    required_args_count = 2
    if len(sys.argv) != required_args_count:
        return 1

    mode = sys.argv[1]
    match mode:
        case "off":
            return disable_password_auth()
        case "on":
            return enable_password_auth()
        case _:
            print("Invalid inner script argument.")
            return 1


if __name__ == "__main__":
    sys.exit(main())
