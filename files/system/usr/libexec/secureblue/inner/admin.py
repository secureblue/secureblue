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

import subprocess
import sys
import os
from typing import Final


def main() -> int:
    """Create new wheel username"""
    required_args_count = 2
    if len(sys.argv) != required_args_count:
        print("Invalid arg count for sandboxed admin function.")
        return 1

    username: Final[str] = sys.argv[1]
    result = subprocess.run(["useradd", "-M", "-G", "wheel", username], check=False)
    if result.returncode != 0:
        print("useradd has failed.")
        return 1
    result = subprocess.run(
        ["passwd", username],
        check=False,
        text=True,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    if result.returncode != 0:
        print("passwd has failed.")
        return 1
    result = subprocess.run(["gpasswd", "-d", str(os.getlogin()), "wheel"], check=False)
    if result.returncode != 0:
        print("gpasswd has failed.")
        return 1

    print(f'A new administrator user has been created called "{username}".')
    return 0


if __name__ == "__main__":
    sys.exit(main())
