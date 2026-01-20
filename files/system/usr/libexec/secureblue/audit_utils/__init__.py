#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Utils for system auditing.
"""

import asyncio
import os
import re

# All subprocess calls we make have trusted inputs and do not use shell=True.
import subprocess  # nosec
import textwrap
from typing import Final

from auditor import AuditError, Status, gettext_marker
from utils import print_err

PASS: Final = Status.PASS
INFO: Final = Status.INFO
WARN: Final = Status.WARN
FAIL: Final = Status.FAIL
UNKNOWN: Final = Status.UNKNOWN


_: Final = gettext_marker()


def warn_if_root() -> None:
    """If run as root, warn that this is not recommended."""
    if not os.getuid():
        print_err("\n" + _("*** WARNING: Running audit script as root is not recommended. ***"))
        print_err(_("*** Some results may be misleading or incomplete. ***") + "\n")


def get_width() -> int:
    """Get the width in columns to be used for reports."""
    try:
        width = min(max(80, os.get_terminal_size().columns), 100)
    except OSError:
        width = 80
    return width


def _format_legend_entry(status: Status, description: str, width: int = 80) -> str:
    """Format legend entry"""
    key_str = f"[{status.to_str_in_color()}]: "
    key_str_width = len(status.name) + 4
    description = re.sub(r"\s+", " ", description.strip())
    lines = textwrap.wrap(description, width=width - key_str_width)
    if not lines:
        return f"{key_str}\n"
    entry = f"{key_str}{lines[0]}\n"
    for line in lines[1:]:
        entry += f"{' ' * key_str_width}{line}\n"
    return entry


def get_legend(width: int = 80) -> str:
    """Get legend to be printed with --help option."""
    legend = _("The following status indicators accompany checks run by the audit script:")
    legend += "\n\n"
    status_descriptions: dict[Status, str] = {
        FAIL: _("check failed - the configuration may be less secure."),
        WARN: _("partial failure, or less significant issue detected."),
        PASS: _("check passed - no problems detected."),
        UNKNOWN: _("unable to perform check (usually due to a file permission issue)."),
    }
    for status, desc in status_descriptions.items():
        legend += _format_legend_entry(status, desc, width)
    legend += "\n"
    legend += _("For flatpak checks, the status indicators have more specific meanings:")
    legend += "\n\n"
    flatpak_status_descriptions: dict[Status, str] = {
        FAIL: _("""app has permissions that can be used as sandbox escapes, allow it to modify
            its own permissions, or otherwise grant very broad access to the system (e.g. access
            to certain directories, direct D-Bus access, X11)."""),
        WARN: _("""app has permissions that have some sandbox escape potential or otherwise
            weaken security (e.g. PulseAudio, Bluetooth, not using hardened_malloc)."""),
        INFO: _("""no potential sandbox escapes detected but some permissions could increase
            attack surface or have privacy implications (e.g. network access)."""),
        PASS: _("no app permissions flagged (however, not all permissions are audited)."),
    }
    for status, desc in flatpak_status_descriptions.items():
        legend += _format_legend_entry(status, desc, width)
    legend += "\n" + textwrap.fill(
        textwrap.dedent(
            _("""\
            Note that some flatpak apps require broad permissions to function. Permissions being
            flagged by the audit script do not necessarily mean that action should be taken.
            """)
        ),
        width=width,
    )
    return legend


class AsyncProcessError(AuditError):
    """An asynchronous subprocess command returned a nonzero exit code."""


async def async_command_stdout(cmd: str, *args: str, check: bool = True) -> str:
    """Asynchronously run a command in the shell and return the contents of stdout."""
    # nosemgrep: dangerous-subprocess-use-audit, dangerous-asyncio-create-exec-audit
    sub = await asyncio.create_subprocess_exec(
        cmd, *args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    await sub.wait()
    # pylint: disable=use-implicit-booleaness-not-comparison-to-zero
    if check and sub.returncode != 0:
        err = f"async command `{cmd} {' '.join(args)}` returned nonzero exit code {sub.returncode}"
        raise AsyncProcessError(err)
    if sub.stdout is None:
        err = f"Failed to get stdout for async command `{cmd} {' '.join(args)}`"
        raise AsyncProcessError(err)
    output = await sub.stdout.read()
    return output.decode("utf-8", errors="replace").strip()


async def get_flatpak_permissions(name: str, version: str) -> str:
    """Get permissions for an installed flatpak."""
    return await async_command_stdout("flatpak", "info", "--show-permissions", name, version)


def validate_sysctl(sysctl: str, actual: str, expected: str) -> bool:
    """Validate a sysctl value against an expected value."""
    actual = re.sub(r"\s+", " ", actual.strip())
    replace = {"disabled": "0", "enabled": "1"}.get(actual)
    if replace is not None:
        actual = replace
    if sysctl == "kernel.sysrq":
        # Both 0 and 4 are secure values for this setting. For details, see:
        # https://www.kernel.org/doc/html/latest/admin-guide/sysrq.html
        return actual in (expected, "0", "4")
    return actual == expected
