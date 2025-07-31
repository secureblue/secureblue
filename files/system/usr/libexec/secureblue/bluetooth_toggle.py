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

'''
Toggles if bluetooth is enabled by creating or deleting "/etc/modprobe.d/99-bluetooth.conf".

arguments:
python3 bluetooth_toggle.py on
    Turns bluetooth on if off, does nothing if already on.

python3 bluetooth_toggle.py off
    Turns bluetooth off if on, does nothing if already off.
'''

from typing import Final
import subprocess
from pathlib import Path
import sys

BLUE_MOD_PATH: Final[str] = "/etc/modprobe.d/"
BLUE_MOD_FILE: Final[str] = "/etc/modprobe.d/99-bluetooth.conf"
BLUE_INNER_SCRIPT: Final[str] = "/usr/libexec/secureblue/bluetooth_toggle-inner.py"

# Copyright (C) 2025 Daniel Hast
# Systemd sandboxing of run0 invocation adapted from run0edit, originally licensed under MIT OR Apache-2.0.
# Used here under the terms of the Apache License 2.0.

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
    "--property=CapabilityBoundingSet=CAP_DAC_OVERRIDE CAP_FOWNER CAP_LINUX_IMMUTABLE",
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

def run_inner(option: int): #0 enables bluetooth, 1 disables
    command: list = ["run0", *SYSTEMD_SANDBOX_PROPERTIES, "python3", BLUE_INNER_SCRIPT, str(option)] 
    try: 
        subprocess.run(command, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"The innerscript failed with return code {e.returncode}")
        return e.returncode
    return 0

def main():
    exists: bool = Path(BLUE_MOD_FILE).exists() 
    if len(sys.argv) == 1: #Toggle mode
        if exists == True: #If file disabling bluetooth kernel modules exists:
            return run_inner(0)
        else:
            return run_inner(1)

    mode = sys.argv[1]
    if mode == "on":
        if exists == False:
            print("Bluetooth already enabled.")
            return 0
        else:
            return run_inner(0)
    if mode == "off":
        if exists == True:
            print("Bluetooth already disabled.")
            return 0
        else:
            return run_inner(1)
    else:
        print("Invalid option selected.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
