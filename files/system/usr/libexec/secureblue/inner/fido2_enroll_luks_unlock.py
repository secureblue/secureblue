# Copyright (C) 2025 The Secureblue Authors
# Rewritten in python by mathbreed. Original bash code by ShadowSlayer1441.
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

import json
import os
import re
import shutil
import subprocess
import sys


# Check whether the string passed follows the pattern of a valid uuid.
def validate_uuid(uuid: str) -> bool:
    pattern = re.compile(r"[a-z0-9]{8}-"
                        "[a-z0-9]{4}-"
                        "[a-z0-9]{4}-"
                        "[a-z0-9]{4}-"
                        "[a-z0-9]{12}")

    return pattern.match(uuid) is not None

# Check if the json passed is valid.
def validate_fido_device(fido_device: str) -> list:
    fido_device = json.loads(fido_device)

    pattern = re.compile(r"/dev/hidraw[0-9]+")

    for i in range(len(fido_device)):
        path = fido_device[i].get("path")
        algo = fido_device[i].get("algorithm")

        if pattern.match(path) is None:
            print("Malformed arguments.")
            sys.exit()

        if algo not in ("es256", "rs256", "eddsa"):
            print("Malformed arguments.")
            sys.exit()

    return fido_device

# Takes uuid and return the file content of the amended crypttab.
def amend_crypttab(uuid: str) -> str:
    # Backup /etc/crypttab
    shutil.copy2("/etc/crypttab", "/etc/crypttab.backup")

    with open("/etc/crypttab.backup", "rb") as crypttab:
        content = crypttab.read()

        # Check if `fido2-device` has already been set
        pattern = re.compile(
                                bytes(
                                    fr"(?<=luks-{uuid} UUID={uuid})"
                                    # Store user-specified options
                                    fr"(?P<options>[-,/ =\w]+)",
                                    encoding="ascii"
                                )
                            )

        target_line = re.search(pattern, content)

        # `fido2-device` has already been set. Return unmodified file.
        if target_line and b"fido2-device" in target_line.group("options"):
            return content

        # Capture all user-specified options in crypttab.
        # And return the amended file content.
        return re.sub(pattern,
            # Append ", fido2-device=auto" to the options captured.
            bytes(r"\1, fido2-device=auto", encoding="ascii"),
            content
        )

def systemd_cryptenroll(additional_args: list[str]) -> str:
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
    with open("/etc/crypttab", "wb") as crypttab:
        crypttab.write(crypttab_content)

    os.chmod("/etc/crypttab", 0o600)
    os.chown("/etc/crypttab", 0, 0)

    print("File '/etc/crypttab' copied to '/etc/crypttab.backup'.\n")

    print(f"The following token(s) are currently enrolled for disk {uuid}:")

    # Print tokens enrolled.
    print(systemd_cryptenroll([]))

    # Visual separator
    print()

    print("Your selected tokens are now enrolled. This may take a while...\n")
    # Enroll selected tokens
    for i in range(len(fido_device)):
        path = fido_device[i].get("path")
        algo = fido_device[i].get("algorithm")
        bio = bool(fido_device[i].get("bio"))

        # Disable PIN entry if biometric authentication is used.
        if bio:
            systemd_cryptenroll(
                [fr"--fido2-device={path}",
                fr"--fido2-credential-algorithm={algo}",
                "--fido2-with-client-pin=no",
                "--fido2-with-user-verification=yes"]
            )
        else:
            systemd_cryptenroll(
                [fr"--fido2-device={path}",
                fr"--fido2-credential-algorithm={algo}"]
            )

    # A list of slots that FIDO tokens are enrolled
    slot_number: list = re.findall("[0-9]+(?= +fido2)", systemd_cryptenroll([]))

    for i in slot_number:
        print(subprocess.run(
            ["/usr/bin/cryptsetup",
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


    ## The following code is taken from files/system/usr/libexec/secureblue/utils/__init__.py ##
    while True:
        try:
            ans = input(
                "Would you like to remove other authentication methods and add a recovery key? [Y/n] "
            ).strip()
            if ans in ("y", "yes", "n", "no"):
                rm_passwd = ans in ("y", "yes")
                break
            print("Please enter y (yes) or n (no).")
        except (KeyboardInterrupt, EOFError):
            print()
            sys.exit(130)

    if rm_passwd:
        # Use enrolled FIDO device to unlock the LUKS device.
        print("Your recovery key: "
            "{systemd_cryptenroll(['--recovery-key', '--unlock-fido2-device=auto'])}")
        print(systemd_cryptenroll(["--wipe-slot=tpm2"]))
        print(systemd_cryptenroll(["--wipe-slot=pkcs11"]))
        print(systemd_cryptenroll(["--wipe-slot=empty"]))
        print(systemd_cryptenroll(["--wipe-slot=password"]))

    print("""
Your recovery key has been created.
Please make backup of the recovery key.

You will have to plug in the FIDO key to unlock your LUKS partition on boot."""
    )


if __name__ == "__main__":
    try:
        if validate_uuid(sys.argv[1]):
            uuid = sys.argv[1]
        fido_device = validate_fido_device(sys.argv[2])
    except IndexError:
        print("Too few arguments given!")
        sys.exit()
    main(uuid, fido_device)
