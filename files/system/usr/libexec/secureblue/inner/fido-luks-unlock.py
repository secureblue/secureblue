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

def main(uuid: str, fido_device: list) -> None:
    print(f"The following tokens are currently enrolled for disk {uuid}:")

    subprocess.run(["systemd-cryptenroll", f"/dev/disk/by-uuid/{uuid}"],
                    capture_output=True,
                    check=True,
                    text=True).stdout.strip()

    for i in fido_device:
        path = fido_device[i].get("path")
        algo = fido_device[i].get("algorithm")
        bio = bool(fido_device[i].get("bio"))

        command = ["systemd-cryptenroll",
                    fr"/dev/disk/by-uuid/{uuid}",
                    fr"--fido2-device={path}",
                    fr"--fido2-credential-algorithm={algo}",]

        # Disable PIN entry if biometric authentication is used.
        if bio:
            command.append("--fido2-with-client-pin=no")
            command.append("--fido2-with-user-verification=yes")

        subprocess.run(command,
                    capture_output=True,
                    check=True,
                    text=True).stdout.strip()

if __name__ == "__main__":
    uuid = validate_uuid(sys.argv[1])
    fido_device = validate_fido_device(sys.argv[2])
    main(uuid, fido_device)
