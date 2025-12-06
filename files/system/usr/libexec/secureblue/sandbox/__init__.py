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
Framework for running rootful functions in a systemd sandbox
"""

import subprocess
import sys
from dataclasses import dataclass, field
from typing import Final

INNER_DIR: Final[str] = "/usr/libexec/secureblue/inner"

# Copyright (C) 2025 Daniel Hast
# Systemd sandboxing of run0 invocation adapted from run0edit, originally licensed
# under MIT OR Apache-2.0. Used here under the terms of the Apache License 2.0.
SYSCALLS_TO_ALLOW: Final[list[str]] = [
    "@system-service"
]
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
    """A class that wraps a function to be run in a sandbox"""

    file_name: str
    capabilities: list[str] = field(default_factory=list, kw_only=True)
    read_write_paths: list[str] = field(default_factory=list, kw_only=True)
    additional_sandbox_properties: list[str] = field(default_factory=list, kw_only=True)
    subprocess_interactive: bool = False

    def __post_init__(self):
        """Ensures list fields have expected types and creates sandbox properties."""
        for prop in (self.capabilities, self.read_write_paths, self.additional_sandbox_properties):
            if not isinstance(prop, list):
                raise ValueError(
                    f"Bad argument to SandboxedFunction: expected list, got `{type(prop)}`."
                )
        subprocess_inter = self.subprocess_interactive
        if not isinstance(subprocess_inter, bool):
            raise ValueError(
                f"Bad argument to SandboxedFunction: expected bool, got `{type(subprocess_inter)}`."
            )

        additional_properties = self.additional_sandbox_properties
        additional_properties = [
            f"--property=CapabilityBoundingSet={' '.join(self.capabilities)}",
            f"--property=ReadWritePaths={' '.join(self.read_write_paths)}"
        ] + additional_properties
        if not all(arg.startswith("--") and arg != "--" for arg in additional_properties):
            raise ValueError("Invalid sandboxing options: options must start with --")


def run(sandboxed_function: SandboxedFunction, *args: str) -> int:
    """Execute a sandboxed function."""

    command = [
        "/usr/bin/run0",
        *RUN0_BASE_ARGUMENTS,
        *sandboxed_function.additional_sandbox_properties,
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
        result = subprocess.run(command, check=False)  # nosec

    return result.returncode
