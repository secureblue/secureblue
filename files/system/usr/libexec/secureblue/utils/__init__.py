#!/usr/bin/python3

# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""
Utils for system auditing.
"""

import asyncio
import enum
import os
import re

# All subprocess calls we make have trusted inputs and do not use shell=True.
import subprocess  # nosec
import sys
import textwrap
from collections.abc import Iterable
from typing import Generator, Final
from auditor import Status, AuditError
import rpm


PASS: Final = Status.PASS
INFO: Final = Status.INFO
WARN: Final = Status.WARN
FAIL: Final = Status.FAIL
UNKNOWN: Final = Status.UNKNOWN


def print_err(text: str):
    """Print text to stderr in bold and red."""
    print(f"\x1b[1m\x1b[31m{text}\x1b[0m", file=sys.stderr)


def warn_if_root():
    """If run as root, warn that this is not recommended."""
    if not os.getuid():
        print_err("\n*** WARNING: Running audit script as root is not recommended. ***")
        print_err("*** Some results may be misleading or incomplete. ***\n")


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
    legend = "The following status indicators accompany checks run by the audit script:\n\n"
    status_descriptions: dict[Status, str] = {
        FAIL: "check failed - the configuration may be less secure.",
        WARN: "partial failure, or less significant issue detected.",
        PASS: "check passed - no problems detected.",
        UNKNOWN: "unable to perform check (usually due to a file permission issue).",
    }
    for status, desc in status_descriptions.items():
        legend += _format_legend_entry(status, desc, width)
    legend += "\nFor flatpak checks, the status indicators have more specific meanings:\n\n"
    flatpak_status_descriptions: dict[Status, str] = {
        FAIL: """app has permissions that can be used as sandbox escapes, allow it to modify
            its own permissions, or otherwise grant very broad access to the system (e.g. access
            to certain directories, direct D-Bus access, X11).""",
        WARN: """app has permissions that have some sandbox escape potential or otherwise
            weaken security (e.g. PulseAudio, Bluetooth, not using hardened_malloc).""",
        INFO: """no potential sandbox escapes detected but some permissions could increase
            attack surface or have privacy implications (e.g. network access).""",
        PASS: "no app permissions flagged (however, not all permissions are audited).",
    }
    for status, desc in flatpak_status_descriptions.items():
        legend += _format_legend_entry(status, desc, width)
    legend += "\n" + textwrap.fill(
        textwrap.dedent(
            """\
            Note that some flatpak apps require broad permissions to function. Permissions being
            flagged by the audit script do not necessarily mean that action should be taken.
            """
        ),
        width=width,
    )
    return legend


def command_stdout(*args: str, check: bool = True) -> str:
    """Run a command in the shell and return the contents of stdout."""
    # We only call this with trusted inputs and do not set shell=True.
    # nosemgrep: dangerous-subprocess-use-audit
    return subprocess.run(args, capture_output=True, check=check, text=True).stdout.strip()  # nosec


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


def command_succeeds(*args: str) -> bool:
    """Run a command in the shell and return the contents of stdout."""
    # We only call this with trusted inputs and do not set shell=True.
    # nosemgrep: dangerous-subprocess-use-audit
    return subprocess.run(args, capture_output=True, check=False).returncode == 0  # nosec


def parse_config(
    stream: Iterable[str], *, sep: str = "=", comment: str = "#"
) -> Generator[tuple[str, str | None]]:
    """
    Parse a text stream as a simple configuration file, yielding a sequence of keys and values
    separated by the given separator ("=" by default).
    """
    for line in stream:
        line = line.strip()
        if not line or line.startswith(comment):
            continue
        split = line.split(sep, maxsplit=1)
        key = split[0].strip()
        if len(split) == 2:
            value = split[1].strip()
        else:
            value = None
        yield key, value


def is_rpm_package_installed(name: str) -> bool:
    """Checks if the given RPM package is installed."""
    ts = rpm.TransactionSet()
    matches = ts.dbMatch("name", name)
    return len(matches) > 0


class Image(enum.Enum):
    """Fedora atomic base image"""

    SILVERBLUE = enum.auto()
    KINOITE = enum.auto()
    SERICEA = enum.auto()
    COSMIC = enum.auto()
    COREOS = enum.auto()

    @classmethod
    def from_image_ref(cls, image_ref: str):
        """Convert an image reference to the corresponding Image enum instance."""
        if "silverblue" in image_ref:
            return cls.SILVERBLUE
        if "kinoite" in image_ref:
            return cls.KINOITE
        if "sericea" in image_ref:
            return cls.SERICEA
        if "cosmic" in image_ref:
            return cls.COSMIC
        if "securecore" in image_ref:
            return cls.COREOS
        return None


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
