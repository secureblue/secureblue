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
Enable or disable an SELinux module.
"""

import enum
import subprocess  # nosec
import sys


class Mode(enum.StrEnum):
    """Enum representing 'enable' or 'disable'."""

    ENABLE = "enable"
    DISABLE = "disable"


def set_module(mode: Mode, module_name: str) -> int:
    """Enable or disable an SELinux module."""
    proc = subprocess.run(["/usr/bin/semodule", f"--{mode}={module_name}"], check=False)  # nosec
    if proc.returncode == 0:
        print(f"SELinux module '{module_name}' {mode}d.")
    return proc.returncode


def main() -> int:
    """Main script entry point."""
    required_args_count = 3
    if len(sys.argv) != required_args_count:
        print("set_selinux_module.py must have exactly two arguments.")
        return 2

    try:
        mode = Mode(sys.argv[1])
    except ValueError:
        print("Invalid argument: first argument must be 'enable' or 'disable'.")
        return 2

    module_name = sys.argv[2]
    return set_module(mode, module_name)


if __name__ == "__main__":
    sys.exit(main())
