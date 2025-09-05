import subprocess
from typing import Final
from .sandboxed_function import SandboxedFunction

INNER_DIR: Final[str] = "/var/home/user/secureblue-dev/files/system/usr/libexec/secureblue/inner"

def create_run0_args(sandboxed_function: SandboxedFunction) -> list[str]:
    """Creates the args for run0."""
    capabilities = sandboxed_function.capabilities()
    read_write_paths = sandboxed_function.read_write_paths()
    if capabilities is None:
        capabilities = "/dev/null"

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

    return systemd_sandbox_properties

def run(sandboxed_function: SandboxedFunction, *args):
    run0_args = create_run0_args(sandboxed_function)
    if run0_args is None or run0_args == [""]:
        return 1
    command = [
        "/usr/bin/run0",
        *run0_args,
        "/usr/bin/python3",
        "-B",  # prevents use of bytecode (pycache) to ease run0 sandboxing configuration
        f"{INNER_DIR}/{sandboxed_function.inner_file_name()}",
        *args
    ]
    result = subprocess.run(command, check=False, text=True, capture_output=True)  # nosec
    if result.returncode != 0:
        print("return code:" + str(result.returncode))
        print("stdout:" + result.stdout)
        print("stderr:" + result.stderr)
        print("subprocess command:" + str(command))
        return None
    print(result.stdout, end="")
    return 0