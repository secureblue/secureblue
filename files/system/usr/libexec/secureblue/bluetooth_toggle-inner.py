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

"""
Handles the priviledges operations to actually change bluetooth kernel modules are loaded.
"""

import sys
import os
from typing import Final

BLUE_MOD_PATH: Final[str] = "/etc/modprobe.d/99-bluetooth.conf"
BLUE_MOD_TEXT: Final[str] = """
install bluetooth /sbin/modprobe --ignore-install bluetooth
install btusb /sbin/modprobe --ignore-install btusb
"""

def main():
    if len(sys.argv) == 1:
        print("An error has occured in calling the inner script.")
        return 1
    
    mode: int = int(sys.argv[1])
    if mode == 0:
        os.remove(BLUE_MOD_PATH)
        print("Bluetooth has been enabled. Reboot for effect.")
        return 0
    if mode == 1:
        with open(BLUE_MOD_PATH, "w") as fd:
            fd.write(BLUE_MOD_TEXT)
        os.chmod(BLUE_MOD_PATH, 0o644)
        print("Bluetooth has been disabled. Reboot for effect.")
        return 0
    else:
        print("Invalid inner script argument(s).")
        return 1


if __name__ == "__main__":
    sys.exit(main())
