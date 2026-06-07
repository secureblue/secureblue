#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import os
import re
import sys
import textwrap
from typing import Final

import inquirer
import sandbox
from fido import ConnectedDevices, CoseAlgorithms
from sandbox import SandboxedFunction
from utils import command_stdout, print_err

SYSTEMD_CRYPTENROLL_SUPPORTED_ALGORITHMS: Final[set] = {
    CoseAlgorithms.EDDSA,
    CoseAlgorithms.ES256,
    CoseAlgorithms.RS256
}

parser = argparse.ArgumentParser(
    prog="ujust setup-luks-fido2-unlock",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent("""
The script makes the following assumptions:
1. '/etc/crypttab' was not manually edited.
2. '/proc/cmdline' should contain exactly one UUID of the target LUKS device.
3. The user will make backup of the recovery key generated, such that if the
   FIDO2 key enrolled is lost, you still have access to the encrypted LUKS device.

---

The script will not make any permanent changes to your system prior to the
authentication stage. If the script fails after you've been asked to authenticate,
you may have to manually revert the changes.
Permanent changes are as follows:
1. '/etc/crypttab' may amended. It's backup is located at '/etc/crypttab.backup'.
2. Tokens and credentials used to encrypt/decrypt your LUKS volume may be added/deleted.
   Run 'systemd-cryptenroll <your LUKS device>' to see the list of tokens enrolled."""),
)

parser.parse_args()


# Given an input_str, find uuid
def find_uuid(lookahead: str, input_str: str) -> str:
    pattern = re.compile(
        rf"{lookahead}"
        "[a-z0-9]{8}-"
        "[a-z0-9]{4}-"
        "[a-z0-9]{4}-"
        "[a-z0-9]{4}-"
        "[a-z0-9]{12}"
    )

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
    if CoseAlgorithms.EDDSA in supported_algo:
        return "eddsa"
    if CoseAlgorithms.ES256 in supported_algo:
        return "es256"
    if CoseAlgorithms.RS256 in supported_algo:
        return "rs256"

    # Should not reach, as incompatible devices should have been excluded.
    return None


connected_devices = ConnectedDevices()

if connected_devices.get_count() == 0:
    print_err("No compatible device detected!")
    sys.exit(0)
elif connected_devices.get_count() == 1:
    print("1 compatible device detected!")
else:
    print(f"{connected_devices.get_count()} compatible devices detected!")

# Warning message for use of multiple FIDO2 tokens with UV.
# Future devs: when you remove these lines, please append `\n`
# to the two print() functions above!
print_err("""
Please note that support for using multiple FIDO2 devices is limited.
If you plan on using the 'user verification' function (e.g. biometric sensors),
it is advised that you only enroll one FIDO2 token.
""")

target_uuid = get_uuid()

connected_devices.prompt_select()

if connected_devices.get_count() == 0:
    print_err("No device selected! Exiting...")
    sys.exit(0)

# Visual separator
print("---\n")

for device in connected_devices.get_devices():
    print(f"Scanning device {device.get_name()}...\n")

    if device.get_cbor_support:
        device.test_supported_algorithm()

        if device.get_supported_algorithms().isdisjoint(SYSTEMD_CRYPTENROLL_SUPPORTED_ALGORITHMS):
            print(f"Device {device.get_name()} is not compatible for use with 'systemd-cryptenroll'.")
            print("This device cannot be used.\n")
            device.close()
            continue

        if device.test_bio_support():
            print(f"Device {device.get_name()} supports biometric authentication.")

            device.set_use_bio(
                inquirer.list_input(
                    "Would you like to use biometric authentication?",
                    choices=[
                        (
                            "Yes (You do NOT have to enter the PIN of your FIDO key on boot.)",
                            True,
                        ),
                        (
                            "No (You WILL have to enter the PIN of your FIDO key on boot)",
                            False,
                        ),
                    ],
                    default=True,
                )
            )

        device.close()
    else:
        print("Automatic detection failed as device does not support CBOR.")
        print("This device cannot be used.\n")
        device.close()

    # Visual separator
    print("---\n")

# Filter out devices without CBOR support
filter(device.get_cbor_support(), connected_devices.get_devices())

print(
    """All devices scanned.
You will now be prompted for authentication.\n
---
"""
)

# Consolidate and serialize things and pass them to the privileged script.
enroll_fido_devices = []

for device in connected_devices.get_devices():
    algorithm = choose_algorithm(device.get_supported_algorithms())

    enroll_fido_devices.append(
        {"path": device.get_path(), "algorithm": algorithm, "bio": device.get_use_bio()}
    )

enroll_fido_devices = json.dumps(enroll_fido_devices)

# Run privileged script.
sandbox.run(
    SandboxedFunction(
        file_name="fido2_enroll_luks_unlock.py",
        capabilities=["CAP_CHOWN"],
        read_write_paths=[
            "/etc/crypttab",
            "/etc/crypttab.backup"
        ],
        allowed_syscalls=["@chown"],
        additional_sandbox_properties=[
            "--property=DeviceAllow=" + f"/dev/disk/by-uuid/{target_uuid}" + "r"
        ],
        remove_sandbox_arguments=["--property=PrivateDevices=yes"],
        subprocess_interactive=True,
    ),
    target_uuid,
    enroll_fido_devices,
)
