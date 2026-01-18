# SPDX-FileCopyrightText: Copyright 2025 Daniel Hast
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Framework for running rootful functions in a systemd sandbox
"""

import subprocess
import sys
from dataclasses import dataclass, field
from typing import Final

# Directory containing privileged workers - change during development!
INNER_DIR: Final[str] = "/usr/libexec/secureblue/inner"

# Systemd sandboxing of run0 invocation adapted from run0edit, originally licensed
# under MIT OR Apache-2.0. Used here under the terms of the Apache License 2.0.
SYSCALLS_TO_ALLOW: Final[list[str]] = ["@system-service"]
SYSCALLS_TO_DENY: Final[list[str]] = [
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
RUN0_BASE_ARGUMENTS: Final[list[str]] = [
    "--property=DevicePolicy=closed",
    "--property=InaccessiblePaths=/run/dbus/ /run/user/",
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
    "--property=RestrictAddressFamilies=AF_UNIX",
    "--property=RestrictNamespaces=yes",
    "--property=RestrictRealtime=yes",
    "--property=RestrictSUIDSGID=yes",
    "--property=SystemCallArchitectures=native",
    f"--property=SystemCallFilter={' '.join(SYSCALLS_TO_ALLOW)}",
    f"--property=SystemCallFilter=~{' '.join(SYSCALLS_TO_DENY)}",
    "--property=SystemCallErrorNumber=EPERM",
]


@dataclass
class SandboxedFunction:
    """A Python worker that runs as root in a sandbox with specified privileges."""

    file_name: str
    """The filename of the privileged worker in INNER_DIR."""

    capabilities: list[str] = field(default_factory=list, kw_only=True)
    """The Linux capabilities to be granted to the worker.

    Optional; defaults to no capabilities.
    """

    read_write_paths: list[str] = field(default_factory=list, kw_only=True)
    """A list of file or directory names to be made writable.

    Optional; defaults to no paths.
    """

    allowed_syscalls: list[str] = field(default_factory=list, kw_only=True)
    """A list of additional syscalls to be granted or denied.

    See systemd.exec(5) and `systemd-analyze syscall-filter`.
    Optional. The default state is `@system-service ~@aio ~@chown ~@keyring ~@memlock
    ~@mount ~@privileged ~@resources ~@setuid ~memfd_create`.
    """

    additional_sandbox_properties: list[str] = field(default_factory=list, kw_only=True)
    """A list of additional run0 *arguments*.

    These typically begin with `--property=`. See run0(1).
    Optional; defaults to no arguments.
    """

    remove_sandbox_arguments: list[str] = field(default_factory=list, kw_only=True)
    """A list of run0 argument terms to fully override the defaults for.

    For example, `["--property=SystemCallFilter"]` will remove all default syscall filters.
    See run0(1). Optional; defaults to no properties.
    """

    subprocess_interactive: bool = field(default=False, kw_only=True)
    """Whether to pass the current stdin, stdout and stderr to the sandbox."""

    def __post_init__(self) -> None:
        """Validate init field values and types.

        Raises:
            ValueError: The value or type of the SandboxedFunction field is invalid.
        """

        # Validate types.
        for prop in (
            self.capabilities,
            self.read_write_paths,
            self.allowed_syscalls,
            self.additional_sandbox_properties,
            self.remove_sandbox_arguments,
        ):
            if not isinstance(prop, list):
                raise ValueError(
                    f"Bad argument to SandboxedFunction: expected list, got `{type(prop)}`."
                )
        subprocess_inter = self.subprocess_interactive
        if not isinstance(subprocess_inter, bool):
            raise ValueError(
                f"Bad argument to SandboxedFunction: expected bool, got `{type(subprocess_inter)}`."
            )

        # All argument fields must contain only strings beginning with '--'.
        prop_args = self.additional_sandbox_properties + self.remove_sandbox_arguments
        if not all(arg.startswith("--") and arg != "--" for arg in prop_args):
            raise ValueError("Invalid sandboxing options: options must start with --")

    def get_arguments(self) -> list[str]:
        """Generate run0 arguments."""

        args = RUN0_BASE_ARGUMENTS.copy()

        # Add args implied by other fields.
        args += [
            f"--property=CapabilityBoundingSet={' '.join(self.capabilities)}",
            f"--property=ReadWritePaths={' '.join(self.read_write_paths)}",
        ]
        if self.allowed_syscalls:
            args.append(f"--property=SystemCallFilter={' '.join(self.allowed_syscalls)}")

        # Remove any args that begin with a term in remove_sandbox_arguments.
        args[:] = [arg for arg in args if not arg.startswith(tuple(self.remove_sandbox_arguments))]

        # Add explicit additional properties.
        args += self.additional_sandbox_properties

        # Suppress red background tint for non-interactive processes.
        if not self.subprocess_interactive and not any(
            arg.startswith("--background") for arg in args
        ):
            args.append("--background=")

        return args

    def run(self, *args: str) -> int:
        """Run the sandboxed function.

        Args:
            *args (str): Positional arguments to pass to the sandboxed function.
        Returns:
            int: The exit status code of the function.
        """

        return run(self, *args)


def run(sandboxed_function: SandboxedFunction, *args: str) -> int:
    """Execute a sandboxed function."""

    command = [
        "/usr/bin/run0",
        *sandboxed_function.get_arguments(),
        "--",
        "/usr/bin/python3",
        "-B",  # prevents use of bytecode (pycache) to ease run0 sandboxing configuration
        f"{INNER_DIR}/{sandboxed_function.file_name}",
        *args,
    ]

    if sandboxed_function.subprocess_interactive:
        result = subprocess.run(
            command, check=False, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr
        )  # nosec
    else:
        result = subprocess.run(command, check=False, stdin=subprocess.DEVNULL)  # nosec

    return result.returncode
