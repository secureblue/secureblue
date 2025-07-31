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

BLUE_MOD_FILE: Final[str] = "/etc/modprobe.d/99-bluetooth.conf"

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
    "CapabilityBoundingSet=CAP_DAC_OVERRIDE CAP_FOWNER CAP_LINUX_IMMUTABLE",
    "DevicePolicy=closed",
    "LockPersonality=yes",
    "MemoryDenyWriteExecute=yes",
    "NoNewPrivileges=yes",
    "PrivateDevices=yes",
    "PrivateIPC=yes",
    "PrivateNetwork=yes",
    "ProcSubset=pid",
    "ProtectClock=yes",
    "ProtectControlGroups=yes",
    "ProtectHostname=yes",
    "ProtectKernelLogs=yes",
    "ProtectKernelModules=yes",
    "ProtectKernelTunables=yes",
    "ProtectProc=noaccess",
    "ReadOnlyPaths=/",
    f"ReadWritePaths={BLUE_MOD_FILE}",
    "RestrictAddressFamilies=AF_UNIX",
    "RestrictNamespaces=yes",
    "RestrictRealtime=yes",
    "RestrictSUIDSGID=yes",
    "SystemCallArchitectures=native",
    "SystemCallFilter=@system-service",
    f"SystemCallFilter=~{' '.join(SYSTEM_CALL_DENY)}",
    "SystemCallErrorNumber=EPERM",
]

def toggle(option: int): #0 disables bluetooth, 1 enables
    if option == 0:
        command: list = ["run0", *SYSTEMD_SANDBOX_PROPERTIES, f"rm -f {BLUE_MOD_FILE}"] 
        try: 
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"run0 rm -f {BLUE_MOD_FILE} failed with return code {e.returncode}")
            return e.returncode
        print("Bluetooth disabled. Reboot for effect.")
        return 0
    if option == 1:
        #Using bash like this is unfortunate but this way avoids multiple run0 invocations 
        #and/or a inner python script being called elevated, and we still get limited run0.
        script = f"""
        echo "install bluetooth /sbin/modprobe --ignore-install bluetooth" >> "{BLUE_MOD_FILE}"
        echo "install btusb /sbin/modprobe --ignore-install btusb" >> "{BLUE_MOD_FILE}"
        chmod 644
        """
        command: list = ["run0", *SYSTEMD_SANDBOX_PROPERTIES, script] 
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"run0 {script} failed with return code {e.returncode}")
            return e.returncode
        print("Bluetooth enabled. Reboot for effect.")
        return 0
    else:
        print("Invalid toggle call")
        return 1

def main():
    exists: bool = Path(BLUE_MOD_FILE).exists() 
    if len(sys.argv) == 1: #Toggle mode
        if exists == True: #If file disabling bluetooth kernel modules exists:
            return toggle(1)
        else:
            return toggle(0)

    mode = sys.argv[1]
    if mode == "on":
        if exists == False:
            print("Bluetooth already enabled.")
            return 0
        else:
            return toggle(1)
    if mode == "off":
        if exists == True:
            print("Bluetooth already disabled.")
            return 0
        else:
            return toggle(0)
    else:
        print("Invalid option selected.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
