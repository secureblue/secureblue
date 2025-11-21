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
The sandboxed admin create function
"""

import grp
import os
import subprocess  # nosec
import sys
from typing import Final


def main() -> int:
    """Create new wheel user"""
    required_args_count = 2
    if len(sys.argv) != required_args_count:
        print("Invalid arg count for sandboxed admin function.")
        return 1

    new_username: Final[str] = sys.argv[1]
    result = subprocess.run(["/usr/sbin/useradd", "-M", "-G", "wheel", new_username], check=False)  # nosec
    if result.returncode != 0:
        print("useradd has failed.")
        return 1
    print("Note passwd will give a bad password warning, this is a known bug and expected.")
    result = subprocess.run(
        ["/usr/sbin/passwd", new_username],
        check=False,
        text=True,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )  # nosec
    if result.returncode != 0:
        print("passwd has failed.")
        return 1

    sudo_user = str(os.environ.get("SUDO_USER"))
    wheel_users = grp.getgrnam("wheel").gr_mem
    if (sudo_user in wheel_users) and (new_username in wheel_users):
        result = subprocess.run(["/usr/sbin/gpasswd", "-d", sudo_user, "wheel"], check=False)  # nosec
        if result.returncode != 0:
            print("gpasswd has failed.")
            return 1
    else:
        print(f'Current user ("{sudo_user}") not in wheel, current user not modified.')

    print(f'A new administrator user has been created called "{new_username}".')
    return 0


if __name__ == "__main__":
    sys.exit(main())
