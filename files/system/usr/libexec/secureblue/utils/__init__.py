#!/usr/bin/python3

# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
from typing import Final

import rpm
from auditor import AuditError, Status, gettext_marker

# Imports for sandbox framework
import inspect
import pickle  # nosec
import base64

PASS: Final = Status.PASS
INFO: Final = Status.INFO
WARN: Final = Status.WARN
FAIL: Final = Status.FAIL
UNKNOWN: Final = Status.UNKNOWN


_: Final = gettext_marker()


def print_err(text: str):
    """Print text to stderr in bold and red."""
    print(f"\x1b[1m\x1b[31m{text}\x1b[0m", file=sys.stderr)


def warn_if_root():
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
    stream: Iterable[str], *, sep: str = "=", comment: str = "#", section_start: str = "["
) -> dict[str, str]:
    """
    Parse a text stream as a simple configuration file with keys and values separated
    by the given separator ("=" by default).
    """
    config = {}
    for raw_line in stream:
        line = raw_line.strip()
        if sep not in line or line.startswith((comment, section_start)):
            continue
        key, value = line.split(sep, maxsplit=1)
        config[key.strip()] = value.strip()
    return config


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


"""
To use and customize this framework you can set the arguements as shown
below in a list passed in the decorator call.
 
Usability Notes:
--Any information passed to the called function could potentially be read
by other processes.
--Your sandboxed must only print to stdout OR return something. This is a 
limitation of subprocess and it's capture_output. You also cannot print a
valid base64 ascii string to stderr in your sandboxed python code.
--To import/use this framework use the follow import statement:
if __name__ == "__main__":
    from utils import sandbox
else: #This prevents recursive imports
    def sandbox(run0):
        def decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator
 
Definitions:
Arg1: Sets ReadWritePaths, which can be None
    Documentation: https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html#ReadWritePaths=
Arg2: Sets CapabilityBoundingSet, which can be None for the default of: 
    CAP_DAC_READ_SEARCH has been chosen as the relatively harmless default (bypass read and execute
    permissions.)
    Documentation: https://www.freedesktop.org/software/systemd/man/latest/systemd-system.conf.html#CapabilityBoundingSet=.
Arg3+:Any arguements after this will be added with "--property=" appended.
    See https://www.freedesktop.org/software/systemd/man/latest/systemd.directives.html for options.
    Notes:  run0 will not accept all of these directives. (No it doesn't appear to be documented which ones
            it does accept.)
            These arguements should not be ReadWritePaths or CapabilityBoundingSet, but it should work.
            If properties are repeated, the latest one will be applied
 
Example(s):
@sandbox(run0=[path, "CAP_DAC_OVERRIDE", IOSchedulingPriority=0])
def delete(recursive: bool, ) -> int:
 
@sandbox(run0[None, None])
def whoami(user: str):
 
Invalid Example(s):
@sandbox
def tick(tac: tuple):
"""


def run0_args(run0: list[str]) -> list[str]:
    """Creates the args for run0."""
    if run0[0] is None:
        run0[0] = "/dev/null"
    if run0[1] is None:
        run0[1] = "CAP_DAC_READ_SEARCH"

    # Copyright (C) 2025 Daniel Hast
    # Systemd sandboxing of run0 invocation adapted from run0edit, originally licensed
    # under MIT OR Apache-2.0. Used here under the terms of the Apache License 2.0.
    SYSTEM_CALL_DENY: list[str] = [
        "@aio",
        "@chown",
        "@keyring",
        "@memlock",
        "@mount",
        "@privileged",
        "@resources",
        "@setuid",
        "memfd_create",
    ]
    SYSTEMD_SANDBOX_PROPERTIES: list[str] = [
        f"--property=CapabilityBoundingSet={run0[1]}",
        "--property=DevicePolicy=closed",
        "--property=LockPersonality=yes",
        "--property=MemoryDenyWriteExecute=yes",
        "--property=NoNewPrivileges=yes",
        "--property=PrivateDevices=yes",
        "--property=PrivateIPC=yes",
        "--property=PrivateNetwork=yes",
        "--property=ProcSubset=pid",
        "--property=ProtectClock=yes",
        "--property=ProtectControlGroups=yes",
        "--property=ProtectHostname=yes",
        "--property=ProtectKernelLogs=yes",
        "--property=ProtectKernelModules=yes",
        "--property=ProtectKernelTunables=yes",
        "--property=ReadOnlyPaths=/",
        "--property=PrivateTmp=yes",
        f"--property=ReadWritePaths={run0[0]}",
        "--property=RestrictAddressFamilies=AF_UNIX",
        "--property=RestrictNamespaces=yes",
        "--property=RestrictRealtime=yes",
        "--property=RestrictSUIDSGID=yes",
        "--property=SystemCallArchitectures=native",
        "--property=SystemCallFilter=@system-service",
        f"--property=SystemCallFilter=~{' '.join(SYSTEM_CALL_DENY)}",
        "--property=SystemCallErrorNumber=EPERM",
    ]

    for property in run0[
        2:
    ]:  # When repeating properties, the latest apply so no need to do anything fancy
        local_property: str = ""
        local_property = "--property=" + property
        SYSTEMD_SANDBOX_PROPERTIES.append(local_property)

    return SYSTEMD_SANDBOX_PROPERTIES


def run0_env(func, *args, **kwargs) -> str:
    """Converts the objects passed to the sandboxed function to base64 ascii."""
    env_data = [func.__name__, inspect.getfile(func), args, kwargs]
    env_str = base64.b64encode(pickle.dumps(env_data)).decode("ascii")
    return f"--setenv=python_config={env_str}"


def sandbox(run0_input: list[str]):
    """Execute the given function with a sandboxed run0."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            """
            This function passes information to the elevated runner via an env var given to run0 called "python_config"
            python_config uses the following list converted in base64 ascii via pickle:
            [function_name,
            function_file_path,
            *args,
            **kwargs]
            """
            run0 = run0_args(run0_input)
            run0.append(run0_env(func, *args, **kwargs))
            if run0 == [""]:
                return 1
            command = [
                "/usr/bin/run0",
                *run0,
                "/usr/bin/python3",
                "-B",  # prevents use of bytecode (pycache) to ease run0 sandboxing configuration
                "/usr/libexec/secureblue/utils/sandbox_inner.py",
            ]
            result = subprocess.run(command, text=True, capture_output=True)  # nosec
            if result.returncode != 0:
                print("return code:" + str(result.returncode))
                print("stdout:" + result.stdout)
                print("stderr:" + result.stderr)
                print("subprocess command:" + str(command))
                return
            print(result.stdout, end="")  # print any text the subprocess tried to print
            b64_str = result.stderr
            try:
                pickle_input_dump = base64.b64decode(b64_str.encode("ascii"))
                func_return = pickle.loads(pickle_input_dump)
                return func_return
            except binascii.Error:
                print(result.stderr, file=sys.stderr)
            return 0

        return wrapper

    return decorator
