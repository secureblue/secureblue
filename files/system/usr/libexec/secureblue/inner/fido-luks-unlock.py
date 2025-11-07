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

# TODO: initramfs thingy

import json
import os
import re
import subprocess
import sys

import inquirer


def validate_uuid(uuid: str) -> str:
    pattern = re.compile(r"[a-z0-9]{8}-"
                        "[a-z0-9]{4}-"
                        "[a-z0-9]{4}-"
                        "[a-z0-9]{4}-"
                        "[a-z0-9]{12}")

    if pattern.match(uuid) is None:
        print("Malformed arguments.")
        sys.exit()
    else:
        return uuid

def validate_fido_device(fido_device: str) -> list:
    fido_device = json.loads(fido_device)

    pattern = re.compile(r"/dev/hidraw[0-9]+")

    for i in fido_device:
        path = fido_device[i].get("path")
        algo = fido_device[i].get("algorithm")

        if pattern.match(path) is None:
            print("Malformed arguments.")
            sys.exit()

        if not ( algo == "es256" | algo == "rs256" | algo == "eddsa" ):
            print("Malformed arguments.")
            sys.exit()

    return fido_device

# Takes uuid and return the file content of the amended crypttab.
def amend_crypttab(uuid: str) -> str:
    # Backup /etc/crypttab
    subprocess.run(["/usr/bin/cp", "/etc/crypttab", "/etc/crypttab.backup"],
                    capture_output=True,
                    check=True,
                    text=True.stdout.strip())

    with open("/etc/crypttab.backup", encoding="ascii") as crypttab:
        content = crypttab.read()

        # Capture all user-specified options in crypttab.
        content = re.sub(fr"(?<=luks-{uuid} UUID={uuid})([-,/ =\w]+)",
            # Append ", fido-device=auto" to the options captured.
            r"\1, fido-device=auto",
            content
        )

        # Return the amended file content.
        return content

def systemd_cryptenroll(additional_args: list) -> str:
    command = ["/usr/bin/systemd-cryptenroll", fr"/dev/disk/by-uuid/{uuid}"]

    command.extend(additional_args)

    return subprocess.run(
        command,
        capture_output=True,
        check=True,
        text=True
    ).stdout.strip()


def main(uuid: str, fido_device: list) -> None:
    # Backup and amend crypttab.
    crypttab_content = amend_crypttab(uuid)

    # Write amended file content to crypttab.
    with open("/etc/crypttab", "w", encoding="ascii") as crypttab:
        crypttab.write(crypttab_content)

    #FIXME - chown root
    os.chmod("/etc/crypttab", 0o600)

    print(r"File '/etc/crypttab' copied to '/etc/crypttab.backup'.\n")

    print(f"The following token(s) are currently enrolled for disk {uuid}:")

    # Print tokens enrolled.
    print(systemd_cryptenroll())

    # Visual separator
    print()

    print("Your selected tokens are now enrolled. This may take a while...\n")
    # Enroll selected tokens
    for i in fido_device:
        path = fido_device[i].get("path")
        algo = fido_device[i].get("algorithm")
        bio = bool(fido_device[i].get("bio"))

        # Disable PIN entry if biometric authentication is used.
        if bio:
            systemd_cryptenroll(
                [fr"--fido-device={path}",
                fr"--fido2-credential-algorithm={algo}",
                "--fido2-with-client-pin=no",
                "--fido2-with-user-verification=yes"]
            )
        else:
            systemd_cryptenroll(
                [fr"--fido-device={path}",
                fr"--fido2-credential-algorithm={algo}"]
            )

    # A list of slots that FIDO tokens are enrolled
    slot_number: list = re.findall("[0-9]+(?= +fido2)", systemd_cryptenroll())

    for i in slot_number:
        print(subprocess.run(
            ["cryptsetup",
             "config",
             "--key-slot",
             fr"{i}",
             "--priority",
             "prefer",
             fr"/dev/disk/by-uuid/{uuid}"],
            capture_output=True,
            check=True,
            text=True
        ).stdout.strip())

    print("---\n")
    print("All tokens enrolled.\n")

    rm_passwd = inquirer.list_input(
                    "Would you like to remove other authentication methods and add a recovery key?",
                    choices=[("Yes", True), ("No", False)]
                )

    if rm_passwd:
        # Use enrolled FIDO device to unlock the LUKS device.
        print(systemd_cryptenroll(["--recovery-key", "--unlock-fido-device=auto"]))
        print(systemd_cryptenroll(["--wipe-slot=tpm2, pkcs11, empty, password"]))

    print("""
Your recovery key has been created.
Please make backup of the recovery key.

You will have to plug in the FIDO key to unlock your LUKS partition on boot.
You may not be prompted if UV is in use."""
    )

if __name__ == "__main__":
    try:
        uuid = validate_uuid(sys.argv[1])
        fido_device = validate_fido_device(sys.argv[2])
    except IndexError:
        print("Too few arguments given!")
        sys.exit()
    main(uuid, fido_device)
