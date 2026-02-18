#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
The sandboxed dhcp hostname sending toggle function
"""

import os
import subprocess
import sys
import time
from typing import Final

HOSTNAME_SENDING_FILE: Final[str] = "/etc/NetworkManager/conf.d/dhcp_no_hostname.conf"
HOSTNAME_SENDING_TEXT: Final[str] = """[connection]
ipv4.dhcp-send-hostname=0
ipv6.dhcp-send-hostname=0
"""


def restart_nm() -> None:
    """Restart the NetworkManager service via systemctl."""
    systemctl = subprocess.run(
        ["/usr/bin/systemctl", "restart", "NetworkManager.service"],
        check=False,
        capture_output=True,
    )

    if not systemctl.returncode:
        return

    time.sleep(3)
    systemctl = subprocess.run(
        ["/usr/bin/systemctl", "restart", "NetworkManager.service"],
        check=False,
        stdout=subprocess.PIPE,
    )

    if systemctl.returncode:
        print("Failed to restart NetworkManager.", file=sys.stderr)
        sys.exit(systemctl.returncode)


def main() -> int:
    """Set or remove the hostname sending block"""
    required_args_count = 2
    if len(sys.argv) != required_args_count:
        return 1

    mode = sys.argv[1]
    match mode:
        case "off":
            with open(HOSTNAME_SENDING_FILE, "w", encoding="utf8") as fd:
                fd.write(HOSTNAME_SENDING_TEXT)
            os.chmod(HOSTNAME_SENDING_FILE, 0o644)
            print("DHCP hostname sending has been disabled. Restarting NetworkManager.")
            restart_nm()
            return 0
        case "on":
            os.remove(HOSTNAME_SENDING_FILE)
            print("DHCP hostname sending has been enabled. Restarting NetworkManager.")
            restart_nm()
            return 0
        case _:
            print("Invalid inner script argument.")
            return 1


if __name__ == "__main__":
    sys.exit(main())
