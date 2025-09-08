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
from typing import Final

from .sandboxed_function import SandboxedFunction

INNER_DIR: Final[str] = "/usr/libexec/secureblue/inner"


def create_run0_args(sandboxed_function: SandboxedFunction) -> list[str]:
    """Creates the args to be passed to run0."""

    capabilities = sandboxed_function.capabilities
    read_write_paths = sandboxed_function.read_write_paths
    additional_sandbox_properties = sandboxed_function.additional_sandbox_properties
    if capabilities is None:
        return None

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
        f"--property=CapabilityBoundingSet={capabilities}",
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

    if read_write_paths is not None:
        systemd_sandbox_properties.append(f"--property=ReadWritePaths={' '.join(read_write_paths)}")

    if additional_sandbox_properties is not None:
        systemd_sandbox_properties += additional_sandbox_properties

    return systemd_sandbox_properties


def run(sandboxed_function: SandboxedFunction, *args):
    """Execute a sandboxed function."""

    run0_args = create_run0_args(sandboxed_function)
    if run0_args is None or run0_args == [""]:
        return 1
    command = [
        "/usr/bin/run0",
        *run0_args,
        "/usr/bin/python3",
        "-B",  # prevents use of bytecode (pycache) to ease run0 sandboxing configuration
        f"{INNER_DIR}/{sandboxed_function.file_name}",
        *args,
    ]
    result = subprocess.run(command, check=False)  # nosec
    return result.returncode
