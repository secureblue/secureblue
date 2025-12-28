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
The wheel user creation implementation for ujust
"""

import pwd
import re
import sys
from typing import Final

import sandbox
from sandbox import SandboxedFunction

# Note this script calls the new user admin in userfacing contexts,
# and wheel internally for clarity.

HELP: Final[str] = """
This script creates a new administrator user, adding them to the wheel
group, for privilege escalation, and the removes the current user from
wheel.

usage:
ujust create-admin
    Asks you for your desired admin username, with a default of "admin".

ujust create-admin <admin_username>

ujust create-admin help
    Prints this message.
"""


def check_username(username: str) -> bool:
    if username in {".", ".."}:
        return False

    # Regex from https://systemd.io/USER_NAMES/ for RHEL/Fedora systems.
    username_pattern = re.compile(r"^[a-zA-Z0-9_.][a-zA-Z0-9_.-]{0,30}[a-zA-Z0-9_.$-]?$")
    return username_pattern.fullmatch(username) is not None


def main() -> int:
    """Handle the arguments and passes them to elevated function"""
    argc = len(sys.argv)
    argc_interactive = 1
    argc_setname = 2

    if argc == argc_interactive:
        username = input("Enter your desired admin username [default: admin]: ") or "admin"
    elif argc == argc_setname:
        username = sys.argv[1]
    else:
        print("Too many options specified, see usage with --help.", file=sys.stderr)
        return 1

    if username == "--help":
        print(HELP)
        return 0
    if not check_username(username):
        print("Your username must be follow RHEL/Fedora rules, see https://systemd.io/USER_NAMES/")
        return 1

    try:
        pwd.getpwnam(username)
        print("New administrator user must not already exist.")
        return 1
    except KeyError:
        admin_function = SandboxedFunction(
            "admin.py",
            subprocess_interactive=True,
            read_write_paths=["/etc"],
            capabilities=["CAP_DAC_OVERRIDE"],
            additional_sandbox_properties=["--property=SystemCallFilter=@chown setuid"],
        )
        return sandbox.run(admin_function, username)


if __name__ == "__main__":
    sys.exit(main())
