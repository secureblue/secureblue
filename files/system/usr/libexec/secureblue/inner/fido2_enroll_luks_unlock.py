#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Sandboxed function that enrolls a FIDO key for use with LUKS device decryption.
"""

import json
import os
import re
import shutil
import subprocess
import sys

from typing import Final
from secureblue.utils import ask_yes_no

CRYPTTAB_FILE: Final[str] = "/etc/crypttab"
CRYPTTAB_FILE_BACKUP: Final[str] = "/etc/crypttab.backup"


# Check whether the string passed follows the pattern of a valid uuid.
def validate_uuid(uuid: str) -> bool:
    pattern = re.compile(
        r"[a-z0-9]{8}-"
        "[a-z0-9]{4}-"
        "[a-z0-9]{4}-"
        "[a-z0-9]{4}-"
        "[a-z0-9]{12}"
    )

    return pattern.match(uuid) is not None


# Check if the json passed is valid.
def validate_fido_device(fido_device: str) -> list:
    fido_device = json.loads(fido_device)

    pattern = re.compile(r"/dev/hidraw[0-9]+")

    for device in fido_device:
        path = device.get("path")
        algo = device.get("algorithm")

        if pattern.match(path) is None:
            print("Malformed arguments.")
            sys.exit()

        if algo not in ("es256", "rs256", "eddsa"):
            print("Malformed arguments.")
            sys.exit()

    return fido_device


# Takes uuid and return
# str: file content of the amended crypttab.
# None: No amendment needs to be made.
def read_crypttab(uuid: str) -> str | None:
    with open(CRYPTTAB_FILE, "rb") as crypttab:
        content = crypttab.read()

        # Check if `fido2-device` has already been set
        pattern = re.compile(
            bytes(
                rf"(?<=luks-{uuid} UUID={uuid})"
                # Store user-specified options
                rf"(?P<options>[-,/ =\w]+)",
                encoding="ascii",
            )
        )

        target_line = re.search(pattern, content)

        # `fido2-device` has already been set.
        if target_line and b"fido2-device" in target_line.group("options"):
            return None

        # Capture all user-specified options in crypttab.
        # And return the amended file content.
        return re.sub(
            pattern,
            # Append ", fido2-device=auto" to the options captured.
            bytes(r"\1, fido2-device=auto", encoding="ascii"),
            content,
        )


def systemd_cryptenroll(additional_args: list[str]) -> str:
    command = ["/usr/bin/systemd-cryptenroll", rf"/dev/disk/by-uuid/{uuid}"]

    command.extend(additional_args)

    return subprocess.run(
        command, capture_output=True, check=True, text=True
    ).stdout.strip()


def main(uuid: str, fido_device: list) -> None:
    crypttab_content = read_crypttab(uuid)

    # Backup and amend crypttab.
    if crypttab_content is not None:
        # Backup /etc/crypttab
        shutil.copy2(CRYPTTAB_FILE, CRYPTTAB_FILE_BACKUP)
        print(f"File '{CRYPTTAB_FILE}' copied to '{CRYPTTAB_FILE_BACKUP}'.\n")

        # Write amended file content to crypttab.
        with open(CRYPTTAB_FILE, "wb") as crypttab:
            crypttab.write(crypttab_content)

    os.chmod(CRYPTTAB_FILE, 0o600)
    os.chown(CRYPTTAB_FILE, 0, 0)

    print(f"The following token(s) are currently enrolled for disk {uuid}:")

    # Print tokens enrolled.
    tokens_enrolled = systemd_cryptenroll([])  # This is a function!
    print(tokens_enrolled)

    # Visual separator
    print()

    print("Your selected tokens is now being enrolled. This may take a while...\n")
    # Enroll selected tokens
    for device in fido_device:
        path = device.get("path")
        algo = device.get("algorithm")
        bio = bool(device.get("bio"))

        # Disable PIN entry if biometric authentication is used.
        if bio:
            systemd_cryptenroll(
                [
                    rf"--fido2-device={path}",
                    rf"--fido2-credential-algorithm={algo}",
                    "--fido2-with-client-pin=no",
                    "--fido2-with-user-verification=yes",
                ]
            )
        else:
            systemd_cryptenroll(
                [rf"--fido2-device={path}", rf"--fido2-credential-algorithm={algo}"]
            )

    # A list of slots that FIDO tokens are enrolled
    slot_number: list = re.findall("[0-9]+(?= +fido2)", tokens_enrolled)

    for i in slot_number:
        print(
            subprocess.run(
                [
                    "/usr/bin/cryptsetup",
                    "config",
                    "--key-slot",
                    rf"{i}",
                    "--priority",
                    "prefer",
                    rf"/dev/disk/by-uuid/{uuid}",
                ],
                capture_output=True,
                check=True,
                text=True,
            ).stdout.strip()
        )

    print("---\n")
    print("All tokens enrolled.\n")

    rm_passwd = ask_yes_no(
        "Would you like to remove other authentication methods and add a recovery key? [Y/n] "
    )

    if rm_passwd:
        # Use enrolled FIDO device to unlock the LUKS device.
        print(
            "Your recovery key: "
            "{systemd_cryptenroll(['--recovery-key', '--unlock-fido2-device=auto'])}"
        )
        print(systemd_cryptenroll(["--wipe-slot=tpm2"]))
        print(systemd_cryptenroll(["--wipe-slot=pkcs11"]))
        print(systemd_cryptenroll(["--wipe-slot=empty"]))
        print(systemd_cryptenroll(["--wipe-slot=password"]))

    print("""
Your recovery key has been created.
Please make backup of the recovery key.

You will have to plug in the FIDO key to unlock your LUKS partition on boot.""")


if __name__ == "__main__":
    try:
        if validate_uuid(sys.argv[1]):
            uuid = sys.argv[1]
        fido_device = validate_fido_device(sys.argv[2])
    except IndexError:
        print("Too few arguments given!")
        sys.exit()
    main(uuid, fido_device)
