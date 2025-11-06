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

# TODO: Make FIDO2 tokens preferred
# TODO: initfs thingy

import json
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
        re.sub(fr"(?<=fido-{uuid} UUID={uuid}\b\w+\b)([- =\w]+)",
            # Ignore lookahead; Append ", fido-device=auto" to the options captured.
            r"\2, fido-device=auto",
            # Store the amended file content back to the variable "content".
            content
        )

        # Return the amended file content.
        return content

def main(uuid: str, fido_device: list) -> None:
    # Backup and amend crypttab.
    crypttab_content = amend_crypttab(uuid)

    # Write amended file content to crypttab.
    with open("/etc/crypttab", "w", encoding="ascii") as crypttab:
        crypttab.write(crypttab_content)

    print(r"File '/etc/crypttab' copied to '/etc/crypttab.backup'.\n")

    print(f"The following token(s) are currently enrolled for disk {uuid}:")

    # Print tokens enrolled.
    command = ["/usr/bin/systemd-cryptenroll", fr"/dev/disk/by-uuid/{uuid}"]

    print(
        subprocess.run(
            command,
            capture_output=True,
            check=True,
            text=True
            )
            .stdout
            .strip()
    )

    # Visual separator
    print()

    print("Your selected tokens are now enrolled. This may take a while...\n")
    # Enroll selected tokens
    for i in fido_device:
        path = fido_device[i].get("path")
        algo = fido_device[i].get("algorithm")
        bio = bool(fido_device[i].get("bio"))

        command = ["/usr/bin/systemd-cryptenroll",
                   fr"/dev/disk/by-uuid/{uuid}",
                   fr"--fido-device={path}",
                   fr"--fido2-credential-algorithm={algo}"]

        # Disable PIN entry if biometric authentication is used.
        if bio:
            command.append("--fido2-with-client-pin=no")
            command.append("--fido2-with-user-verification=yes")

        subprocess.run(command,
                    capture_output=True,
                    check=True,
                    text=True).stdout.strip()

    print("---\n")
    print("All tokens enrolled.\n")

    rm_passwd = inquirer.list_input(
                    "Would you like to remove other authentication methods and add a recovery key?",
                    choices=[("Yes", True), ("No", False)]
                )

    if rm_passwd:
        subprocess.run(
            ["/usr/bin/systemd-cryptenroll",
             fr"/dev/disk/by-uuid/{uuid}",
             "--recovery-key",
             # Make the user use enrolled FIDO device to unlock the LUKS device.
             "--unlock-fido-device=auto"],
            capture_output=True,
            check=True,
            text=True
        ).stdout.strip()

        subprocess.run(
            ["/usr/bin/systemd-cryptenroll",
             fr"/dev/disk/by-uuid/{uuid}",
             "--wipe-slot=tpm2, pkcs11, empty, password"],
            capture_output=True,
            check=True,
            text=True
        ).stdout.strip()

    print("""
Your recovery key has been created.
Please make backup of the recovery key.

You will have to plug in the FIDO key to unlock your LUKS partition on boot.
You may not be prompted if UV is in use."""
    )

if __name__ == "__main__":
    uuid = validate_uuid(sys.argv[1])
    fido_device = validate_fido_device(sys.argv[2])
    main(uuid, fido_device)
