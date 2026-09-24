#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Install Dangerzone (sandboxed PDF sanitizer): https://dangerzone.rocks/
"""

import subprocess
import sys
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from files.system.usr.libexec.secureblue.utils import ask_yes_no, print_wrapped
else:
    from utils import ask_yes_no, print_wrapped

WARNING_MESSAGE: Final[str] = """
Warning: Dangerzone (https://dangerzone.rocks/) requires enabling both container-domain
user namespace creation and container-domain ptrace. This is a security tradeoff, as
other programs on your system will also be able to use container tools such as podman
and to use ptrace to inspect child processes in containers.
"""


def main() -> int:
    """Main script entrypoint."""

    try:
        subprocess.run(
            ["/usr/bin/rpm", "-q", "dangerzone"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except subprocess.CalledProcessError:
        print("Dangerzone is not installed on this system. Unable to enable Dangerzone.")
        return 1

    print_wrapped(WARNING_MESSAGE)
    if not ask_yes_no("Continue to enable Dangerzone?"):
        print("Canceling.")
        return 0

    try:
        print("Enabling container-domain user namespace creation...")
        subprocess.run(["/usr/bin/ujust", "set-container-userns", "on"], check=True)
        print("Ensuring ptrace is allowed in containers...")
        subprocess.run(["/usr/bin/ujust", "set-ptrace", "container"], check=True)
    except subprocess.CalledProcessError:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
