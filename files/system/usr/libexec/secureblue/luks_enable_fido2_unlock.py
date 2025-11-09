# Copyright (C) 2025 The Secureblue Authors
# Rewritten in python by mathbreed. Original bash code by ShadowSlayer1441.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

import argparse
import json
import os
import re
import sys
import textwrap

import inquirer
import sandbox
from fido import ConnectedDevices
from sandbox import SandboxedFunction
from utils import command_stdout, print_err

parser = argparse.ArgumentParser(prog="ujust setup-luks-fido2-unlock",
                                 formatter_class=argparse.RawDescriptionHelpFormatter,

                                 description=textwrap.dedent("""
The script makes the following assumptions:
1. '/etc/crypttab' was not manually edited.
2. '/proc/cmdline' should contain exactly one UUID of the target LUKS device.
3. The user will make backup of the recovery key generated.
   Such that if the FIDO2 key enrolled is lost, you still have access to the LUKS device.

---

The script will not make any permanent changes to your system prior to the authentication stage.
If the script fails after you're asked to authenticate, you may have to manually revert the changes.
Permanent changes are as follows:
1. '/etc/crypttab' is amended. You may find it's backup at '/etc/crypttab.backup'.
2. Tokens and credentials used to encrypt/decrypt your LUKS volume may be added/deleted.
   Run 'systemd cryptenroll <your LUKS device>' for a list of all tokens enrolled."""))

parser.parse_args()

# Given an input_str, find uuid
def find_uuid(lookahead: str, input_str: str) -> str:
    pattern = re.compile(fr"{lookahead}"
                        "[a-z0-9]{8}-"
                        "[a-z0-9]{4}-"
                        "[a-z0-9]{4}-"
                        "[a-z0-9]{4}-"
                        "[a-z0-9]{12}")

    matched = re.findall(pattern, input_str)

    if len(matched) != 1:
        print("NOT SUPPORTED")
        sys.exit(0)

    return matched[0]

def get_uuid() -> str:
    with open("/proc/cmdline", encoding="ascii") as kargs:
        line = kargs.read()
        device_uuid = find_uuid("(?<=rd.luks.uuid=luks-)", line)

    # Validation
    lsblk = command_stdout("/usr/bin/lsblk", "-o", "NAME")

    if device_uuid not in lsblk:
        print_err(f"Could not find device {device_uuid} in 'lsblk'.")
        sys.exit(0)

    if not os.path.exists(f"/dev/disk/by-uuid/{device_uuid}"):
        print_err("Could not find block device with UUID: {device_uuid}.")
        sys.exit(0)

    return device_uuid

def choose_algorithm(supported_algo: set) -> str | None:
    if "EDDSA" in supported_algo:
        return "eddsa"
    if "ES256" in supported_algo:
        return "es256"
    if "RS256" in supported_algo:
        return "rs256"
    return None # Device is not supported!


connected_devices = ConnectedDevices()

if connected_devices.connected_device_count == 0:
    print_err("No compatible device detected!")
    sys.exit(0)
elif connected_devices.connected_device_count == 1:
    print("1 compatible device detected!")
else:
    print(f"{connected_devices.connected_device_count} compatible devices detected!")

# Warning message for use of multiple FIDO2 tokens with UV.
# For future devs: when you remove these lines, please append `\n` to the two print() functions above!
print_err("""
Please note that support for using multiple FIDO2 devices is limited.
If you plan on using the 'user verification' function (e.g. biometric sensors),
it is advised that you only enroll one FIDO2 token.
""")

target_uuid = get_uuid()

connected_devices.prompt_select()

if len(connected_devices.selected) == 0:
    print_err("No device selected!")
    sys.exit(0)

# The set consist of indices (**as in ConnectedDevice.devices**) to be removed from ConnectedDevices.selected.
# If ConnectedDevices.selected = [1, 3, 4],
# If remove_selected = {3}, the element 3 in the array will be removed, leaving [1, 4].
remove_selected = {}

# Visual separator
print("---\n")

for i in connected_devices.selected:
    device = connected_devices.devices[i]

    print(f"Scanning device {device.name}...\n")

    if device.cbor:
        if device.test_supported_algorithm() == {}:
            print(f"Device {device.name} is not compatible for use with 'systemd-cryptenroll'.")
            print("This device will not be used.\n")
            device.device.close()
            remove_selected.add(i)
            continue

        if device.test_bio_support():
            print(f"Device {device.name} supports biometric authentication.")

            use_bio = inquirer.list_input("Would you like to use biometric authentication?",
                          choices=[("Yes (You do NOT have to enter the PIN of your FIDO key on boot.)", True),
                                   ("No (You WILL have to enter the PIN of your FIDO key on boot)", False)],
                          default=True)

            if use_bio:
                print()
                device.set_bio_support()

        device.device.close()
    else:
        print("Automatic detection failed as device does not support CBOR.")
        print("This device will not be used.\n")
        device.device.close()
        remove_selected.add(i)

    # Visual separator
    print("---\n")

for i in remove_selected:
    # Use of remove() is okay as all elements in ConnectedDevices.selected should be unique.
    connected_devices.selected.remove(i)

print(
"""All devices scanned.
You will now be prompted for authentication.\n
---
""")

# Consolidate and serialize things and pass them to the privileged script.
enroll_fido_devices = []

for i in connected_devices.selected:
    device = connected_devices.devices[i] # FidoDevice instance
    algorithm = choose_algorithm(device.supported_algorithm)

    enroll_fido_devices.append({"path": device.get_path(),
                                "algorithm": algorithm,
                                "bio": device.bio})

enroll_fido_devices = json.dumps(enroll_fido_devices)

# Run privileged script.
sandbox.run(
    SandboxedFunction(
        "fido2_enroll_luks_unlock.py",
        read_write_paths=["/etc"]
    ),
    target_uuid,
    enroll_fido_devices,
)
