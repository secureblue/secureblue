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
Install Dangerzone (sandboxed PDF sanitizer): https://dangerzone.rocks/
"""

import subprocess  # nosec
import sys
from typing import Final

import sandbox
from utils import ask_yes_no, print_wrapped

WARNING_MESSAGE: Final[str] = """
Warning: Dangerzone (https://dangerzone.rocks/) requires enabling both container-domain
user namespace creation and (restricted) ptrace. This is a security tradeoff, as other
programs on your system will also be able to use container tools such as podman and to
use ptrace to inspect child processes.
"""


def main() -> int:
    """Main script entrypoint."""
    print_wrapped(WARNING_MESSAGE)
    if not ask_yes_no("Continue installing Dangerzone?"):
        print("Canceling installation.")
        return 0

    inner_script = sandbox.SandboxedFunction(
        "dangerzone.py",
        read_write_paths=[
            "/etc/yum.repos.d/dangerzone.repo",
            "/etc/containers/policy.json",
            "/etc/sysctl.d/61-ptrace-scope.conf",
        ],
        capabilities=["CAP_DAC_OVERRIDE"],
    )
    exit_code = sandbox.run(inner_script)
    if exit_code != 0:
        return exit_code
    print("Enabling container-domain user namespace creation...")
    proc = subprocess.run(["/usr/bin/ujust", "set-container-userns", "on"], check=False)  # nosec
    if proc.returncode != 0:
        return proc.returncode
    print("Installing Dangerzone as layered package...")
    proc = subprocess.run(["/usr/bin/rpm-ostree", "install", "dangerzone"], check=False)  # nosec
    if proc.returncode != 0:
        return proc.returncode
    print("Reboot to complete the installation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
