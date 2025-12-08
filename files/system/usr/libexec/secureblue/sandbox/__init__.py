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

import dataclasses
import subprocess
import sys
from typing import Final

INNER_DIR: Final[str] = "/usr/libexec/secureblue/inner"


@dataclasses.dataclass
class SandboxedFunction:
    """A class that wraps a function to be run in a sandbox"""

    file_name: str
    capabilities: list[str] = dataclasses.field(default_factory=list, kw_only=True)
    read_write_paths: list[str] = dataclasses.field(default_factory=list, kw_only=True)
    additional_sandbox_properties: list[str] = dataclasses.field(default_factory=list, kw_only=True)
    remove_sandbox_properties: list[str] = dataclasses.field(default_factory=list, kw_only=True)
    subprocess_interactive: bool = False

    def __post_init__(self):
        """Ensures list fields have expected types."""
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


def create_run0_options(sandboxed_function: SandboxedFunction) -> list[str]:
    """Creates the options to be passed to run0."""

    capabilities = sandboxed_function.capabilities
    read_write_paths = sandboxed_function.read_write_paths
    additional_sandbox_properties = sandboxed_function.additional_sandbox_properties

    # Copyright (C) 2025 Daniel Hast
    # Systemd sandboxing of run0 invocation adapted from run0edit, originally licensed
    # under MIT OR Apache-2.0. Used here under the terms of the Apache License 2.0.
    system_calls_to_deny: list[str] = [
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
    systemd_sandbox_properties: list[str] = [
        f"--property=CapabilityBoundingSet={' '.join(capabilities)}",
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
        "--property=SystemCallFilter=@system-service",
        f"--property=SystemCallFilter=~{' '.join(system_calls_to_deny)}",
        "--property=SystemCallErrorNumber=EPERM",
    ]

    for prop in sandboxed_function.remove_sandbox_properties:
        prop_arg = f"--property={prop}"
        if prop_arg in systemd_sandbox_properties:
            systemd_sandbox_properties.remove(prop_arg)

    systemd_sandbox_properties.append(f"--property=ReadWritePaths={' '.join(read_write_paths)}")
    systemd_sandbox_properties += additional_sandbox_properties

    # Suppress red background tint for non-interactive processes
    if not sandboxed_function.subprocess_interactive and not any(
        arg.startswith("--background") for arg in additional_sandbox_properties
    ):
        systemd_sandbox_properties.append("--background=")

    return systemd_sandbox_properties


def run(sandboxed_function: SandboxedFunction, *args: str) -> int:
    """Execute a sandboxed function."""

    run0_options = create_run0_options(sandboxed_function)
    if not run0_options:
        raise ValueError("Must not have empty list of options to pass to run0.")
    if not all(arg.startswith("--") and arg != "--" for arg in run0_options):
        raise ValueError("Invalid sandboxing options: options must start with --")
    command = [
        "/usr/bin/run0",
        *run0_options,
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
