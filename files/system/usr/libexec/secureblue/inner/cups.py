#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import subprocess
import sys
from typing import Final

UNITS: Final[list[str]] = [
    "cups.service",
    "cups.socket",
]

MASK_UNITS: Final[list[str]] = [
    *UNITS,
    "avahi-daemon.service",
    "avahi-daemon.socket",
]

NOTE: Final[str] = """\
CUPS enabled.
avahi-daemon is unmasked & will be started as needed on an on-demand basis.

Note: cups-browsed, the printer discovery service, is still disabled for
security reasons. New network printers will need to be added manually.
If you absolutely need network discovery, you can enable the cups-browsed
service at your own risk. Secureblue strongly recommends against this."""


def enable_cups() -> None:
    subprocess.run(
        [
            "/usr/bin/firewall-cmd",
            "--permanent",
            "--add-port=631/tcp",
            "--add-port=631/udp",
            "--quiet",
        ],
        check=True,
    )
    subprocess.run(["/usr/bin/firewall-cmd", "--reload", "--quiet"], check=True)
    subprocess.run(["/usr/bin/systemctl", "unmask", "--quiet", *MASK_UNITS], check=True)
    subprocess.run(["/usr/bin/systemctl", "enable", "--now", "--quiet", *UNITS], check=True)
    subprocess.run(["/usr/bin/systemctl", "daemon-reload"], check=True)


def disable_cups() -> None:
    subprocess.run(
        [
            "/usr/bin/firewall-cmd",
            "--permanent",
            "--remove-port=631/tcp",
            "--remove-port=631/udp",
            "--quiet",
        ],
        check=True,
    )
    subprocess.run(["/usr/bin/firewall-cmd", "--reload", "--quiet"], check=True)
    subprocess.run(["/usr/bin/systemctl", "disable", "--now", "--quiet", *UNITS], check=True)
    subprocess.run(["/usr/bin/systemctl", "mask", "--now", "--quiet", *MASK_UNITS], check=True)
    subprocess.run(["/usr/bin/systemctl", "daemon-reload"], check=True)


def main() -> int:
    required_args_count = 2
    if len(sys.argv) != required_args_count:
        return 1

    mode = sys.argv[1].casefold()
    try:
        match mode:
            case "on":
                enable_cups()
                print(NOTE)
                return 0
            case "off":
                disable_cups()
                print("CUPS & avahi-daemon disabled.")
                return 0
            case _:
                print("Please provide a valid argument (on/off).")
                return 1
    except subprocess.CalledProcessError:
        print("An unexpected error occured.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
