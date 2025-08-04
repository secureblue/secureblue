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

import subprocess  # nosec
import sys
from pathlib import Path
from typing import Final

BLUE_MOD_PATH: Final[str] = "/etc/modprobe.d/"
BLUE_HELP: Final[str] = """
This python script toggles if bluetooth is enabled by creating or deleting a modprobe file at
"/etc/modprobe.d/99-bluetooth.conf" to disable or enable the kernel modules
needed for Bluetooth. Note this change only takes affect upon reboot.

usage:
ujust toggle-bluetooth-modules
    Toggles Bluetooth.

ujust toggle-bluetooth-modules on
    Turns Bluetooth on, does nothing if already on.

ujust toggle-bluetooth-modules off
    Turns Bluetooth off, does nothing if already off.

ujust toggle-bluetooth-modules status
    Reports if Bluetooth is set on or off.

ujust toggle-bluetooth-modules --help
    Prints this message.
"""
# Note: If you are running this python script standalone use 'python3 bluetooth_toggle.py <option>'

BLUE_MOD_FILE: Final[str] = "/etc/modprobe.d/99-bluetooth.conf"
BLUE_INNER_SCRIPT: Final[str] = "/usr/libexec/secureblue/bluetooth_toggle_inner.py"

# Copyright (C) 2025 Daniel Hast
# Systemd sandboxing of run0 invocation adapted from run0edit, originally licensed
# under MIT OR Apache-2.0. Used here under the terms of the Apache License 2.0.

SYSTEM_CALL_DENY: Final[list[str]] = [
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

SYSTEMD_SANDBOX_PROPERTIES: Final[list[str]] = [
    "--property=CapabilityBoundingSet=CAP_DAC_OVERRIDE",
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
    "--property=ProtectProc=noaccess",
    "--property=ReadOnlyPaths=/",
    f"--property=ReadWritePaths={BLUE_MOD_PATH}",
    "--property=RestrictAddressFamilies=AF_UNIX",
    "--property=RestrictNamespaces=yes",
    "--property=RestrictRealtime=yes",
    "--property=RestrictSUIDSGID=yes",
    "--property=SystemCallArchitectures=native",
    "--property=SystemCallFilter=@system-service",
    f"--property=SystemCallFilter=~{' '.join(SYSTEM_CALL_DENY)}",
    "--property=SystemCallErrorNumber=EPERM",
]


def run_inner(enable: bool) -> int:
    command: list = [
        "/usr/bin/run0",
        *SYSTEMD_SANDBOX_PROPERTIES,
        "/usr/bin/python3",
        BLUE_INNER_SCRIPT,
        str(int(enable)),
    ]
    try:
        subprocess.run(command, text=True, check=True) # nosec
    except subprocess.CalledProcessError as e:
        print(f"The inner script failed with return code {e.returncode}.")
        return e.returncode
    return 0


def is_module_loaded(module_name: str) -> bool:
    try:
        with open("/proc/modules", encoding="utf8") as fd:
            return any(line.startswith(module_name + " ") for line in fd)
    except OSError:
        return False


def status(disabled: bool):
    message: str = ""
    if not is_module_loaded("bluetooth") and not is_module_loaded("btusb"):
        message += "Bluetooth is disabled currently"
    else:
        message += "Bluetooth is enabled currently"
    if disabled:
        message += ", and after a reboot, Bluetooth will be disabled."
    else:
        message += ", and after a reboot. Bluetooth will be enabled."
    print(message)


def main(): #noqa: C901
    disabled: bool = Path(
        BLUE_MOD_FILE
    ).exists()  # If this file exists, we assume the Bluetooth kernel modules are already disabled.
    if len(sys.argv) == 1:  # Toggle mode
        if disabled:
            return run_inner(True)
        return run_inner(False)

    mode = sys.argv[1]
    match mode:
        case "on":
            if not disabled:
                status(disabled)
            else:
                return run_inner(True)
        case "off":
            if disabled:
                status(disabled)
            else:
                return run_inner(False)
        case "status":
            status(disabled)
        case "--help":
            print(BLUE_HELP)
        case _:
            print("Invalid option selected. Try --help.")
            return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
