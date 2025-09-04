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
    Notes:  run0 will not accept all of these directives. (No it doesn't appear to be documented
            which ones it does accept.)
            These arguements should not be ReadWritePaths or CapabilityBoundingSet, but it
            should work. If properties are repeated, the latest one will be applied

Example(s):
@sandbox(run0=[path, "CAP_DAC_OVERRIDE", IOSchedulingPriority=0])
def delete(recursive: bool, ) -> int:

@sandbox(run0[None, None])
def whoami(user: str):

Invalid Example(s):
@sandbox
def tick(tac: tuple):
"""
import subprocess


class Inner:
    BLUETOOTH = "bluetooth.py"

INNER_DIR = "/usr/libexec/secureblue/inner"

def create_run0_args(capabilities: str) -> list[str]:
    """Creates the args for run0."""
    if capabilities is None:
        capabilities = "/dev/null"

    # Copyright (C) 2025 Daniel Hast
    # Systemd sandboxing of run0 invocation adapted from run0edit, originally licensed
    # under MIT OR Apache-2.0. Used here under the terms of the Apache License 2.0.
    system_call_deny: list[str] = [
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
        # "--property=ReadOnlyPaths=/",
        # "--property=PrivateTmp=yes",
        # f"--property=ReadWritePaths={run0[0]}",
        "--property=RestrictAddressFamilies=AF_UNIX",
        "--property=RestrictNamespaces=yes",
        "--property=RestrictRealtime=yes",
        "--property=RestrictSUIDSGID=yes",
        "--property=SystemCallArchitectures=native",
        "--property=SystemCallFilter=@system-service",
        f"--property=SystemCallFilter=~{' '.join(system_call_deny)}",
        "--property=SystemCallErrorNumber=EPERM",
    ]

    return systemd_sandbox_properties

def run(sandboxed_function, capabilities, *args):
    run0_args = create_run0_args(capabilities)
    if run0_args is None or run0_args == [""]:
        return 1
    command = [
        "/usr/bin/run0",
        *run0_args,
        "/usr/bin/python3",
        "-B",  # prevents use of bytecode (pycache) to ease run0 sandboxing configuration
        f"{INNER_DIR}/{sandboxed_function}",
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


