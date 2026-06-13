#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Enable or disable CUPS."""

from typing import Final
import subprocess
import sys

import utils

CommandUsageError: Final = utils.CommandUsageError
ToggleMode: Final = utils.ToggleMode
parse_basic_toggle_args: Final = utils.parse_basic_toggle_args
SystemdService: Final = utils.SystemdService

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
service at your own risk. Secureblue strongly recommends against this.
"""

HELP_MESSAGE: Final[str] = """\
Enable or disable CUPS.

Usage:
ujust set-cups
    Enables or disables interactively based on the user's preference.

ujust set-cups on
    Enables CUPS; does nothing if already on.

ujust set-cups off
    Disables CUPS; does nothing if already off.

ujust set-cups status
    Reports if CUPS is enabled or disabled.

ujust set-cups --help
    Prints this message.
"""


def run(mode: ToggleMode) -> int:
    mode = ToggleMode(mode)
    if mode == ToggleMode.HELP:
        print(HELP_MESSAGE)
        return 0

    cups_enabled = SystemdService("cups").is_enabled()

    match mode:
        case ToggleMode.STATUS:
            print("Enabled" if cups_enabled else "Disabled")
        case ToggleMode.ON:
            if cups_enabled:
                print("CUPS is already enabled.")
            else:
                subprocess.run(["/usr/bin/firewall-cmd", "--permanent", "--add-port=631/tcp"], check=True)
                subprocess.run(["/usr/bin/firewall-cmd", "--permanent", "--add-port=631/udp"], check=True)
                subprocess.run(["/usr/bin/firewall-cmd", "--reload"], check=True)
                subprocess.run(["/usr/bin/systemctl", "unmask", *MASK_UNITS], check=True)
                SystemdService(*UNITS).enable_now("--system")
                subprocess.run(["/usr/bin/systemctl", "daemon-reload"], check=True)
                print(NOTE)
        case ToggleMode.OFF:
            if cups_enabled:
                subprocess.run(["/usr/bin/firewall-cmd", "--permanent", "--remove-port=631/tcp"], check=True)
                subprocess.run(["/usr/bin/firewall-cmd", "--permanent", "--remove-port=631/udp"], check=True)
                subprocess.run(["/usr/bin/firewall-cmd", "--reload"], check=True)
                SystemdService(*UNITS).disable_now("--system")
                subprocess.run(["/usr/bin/systemctl", "mask", "--now", *MASK_UNITS], check=True)
                subprocess.run(["/usr/bin/systemctl", "daemon-reload"], check=True)
                print("CUPS & avahi-daemon disabled.")
            else:
                print("CUPS is already disabled.")

    return 0


def main() -> int:
    try:
        mode = parse_basic_toggle_args(prompt="Would you like CUPS to be enabled?")
    except CommandUsageError as e:
        print(f"Usage error: {e}. See usage with --help.")
        return 2
    return run(mode)


if __name__ == "__main__":
    sys.exit(main())
