#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
# SPDX-License-Identifier: Apache-2.0

"""Enable, disable, or check status of libvirt daemons."""

import itertools
import subprocess  # nosec
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from utils import (
    CommandUsageError,
    ToggleMode,
    command_stdout,
    parse_basic_toggle_args,
)

HELP_MESSAGE: Final[str] = """\
Toggles if libvirt daemons are enabled. For further documentation, see:
    https://libvirt.org/daemons.html

usage:
ujust set-libvirt-daemons
    Enables or disables interactively based on the user's preference.

ujust set-libvirt-daemons on
    Enables and starts libvirt daemons.

ujust set-libvirt-daemons off
    Disables and stops libvirt daemons.

ujust set-libvirt-daemons status
    Reports status of libvirt daemons.

ujust set-libvirt-daemons --help
    Prints this message.
"""

QEMU_DRIVER: Final[str] = "virtqemud"

LIBVIRT_MODULAR_DRIVERS: Final[list[str]] = [
    "virtqemud",
    "virtinterfaced",
    "virtnetworkd",
    "virtnodedevd",
    "virtnwfilterd",
    "virtsecretd",
    "virtstoraged",
]

LIBVIRT_OTHER_DAEMONS: Final[dict[str, Sequence[str]]] = {
    "virtlogd": ("", "-admin"),
    "virtlockd": ("", "-admin"),
    "virtproxyd": ("", "-ro", "-admin"),
}

LIBVIRT_SERVICES: Final[list[str]] = [
    f"{daemon}.service"
    for daemon in itertools.chain(LIBVIRT_MODULAR_DRIVERS, LIBVIRT_OTHER_DAEMONS.keys())
]
LIBVIRT_SOCKETS: Final[list[str]] = [
    f"{driver}{suffix}.socket"
    for driver in LIBVIRT_MODULAR_DRIVERS
    for suffix in ("", "-ro", "-admin")
] + [
    f"{daemon}{suffix}.socket"
    for daemon, suffixes in LIBVIRT_OTHER_DAEMONS.items()
    for suffix in suffixes
]


def _systemd_units_status(*names: str) -> list[str]:
    """Get systemd unit status."""
    output = command_stdout("/usr/bin/systemctl", "is-enabled", "--", *names, check=False)
    return output.splitlines()


@dataclass
class LibvirtDaemonStatus:
    """Status of a libvirt daemon."""

    name: str
    service_status: str
    socket_status: str
    socket_ro_status: str
    socket_admin_status: str

    @classmethod
    def current_status(cls, name: str) -> "LibvirtDaemonStatus":
        (service_status, socket_status, socket_ro_status, socket_admin_status) = (
            _systemd_units_status(
                f"{name}.service", f"{name}.socket", f"{name}-ro.socket", f"{name}-admin.socket"
            )
        )
        return LibvirtDaemonStatus(
            name=name,
            service_status=service_status,
            socket_status=socket_status,
            socket_ro_status=socket_ro_status,
            socket_admin_status=socket_admin_status,
        )

    @staticmethod
    def header_row(column_width: int = 15) -> str:
        columns = [
            format(s, f"<{column_width}") for s in ("driver", ".service", ".socket", "-ro.socket")
        ] + ["-admin.socket"]
        return "| ".join(columns)

    def status_row(self, column_width: int = 15) -> str:
        """Format as row for printing in a table."""
        socket_ro_status = self.socket_ro_status.replace("not-found", "N/A")
        columns = [
            format(s, f"<{column_width}")
            for s in (self.name, self.service_status, self.socket_status, socket_ro_status)
        ] + [self.socket_admin_status]
        return "| ".join(columns)


def print_libvirt_status(column_width: int = 15) -> None:
    """Print status of libvirt modular daemons."""
    print(LibvirtDaemonStatus.header_row(column_width))
    print("-" * ((column_width + 2) * 5))
    for daemon in itertools.chain(LIBVIRT_MODULAR_DRIVERS, LIBVIRT_OTHER_DAEMONS):
        status = LibvirtDaemonStatus.current_status(daemon)
        print(status.status_row(column_width))


def enable_libvirt_daemons() -> int:
    """Enable and start libvirt modular daemons."""
    result = subprocess.run(
        ["/usr/bin/systemctl", "enable", "--now", f"{QEMU_DRIVER}.service", *LIBVIRT_SOCKETS],
        check=False,
    )  # nosec
    return result.returncode


def disable_libvirt_daemons() -> int:
    """Disable and start libvirt modular daemons."""
    result = subprocess.run(
        ["/usr/bin/systemctl", "disable", "--now", *LIBVIRT_SERVICES, *LIBVIRT_SOCKETS],
        check=False,
    )  # nosec
    return result.returncode


def run(mode: ToggleMode) -> int:
    """Run the logic for enabling or disabling unconfined-domain userns."""
    match mode:
        case ToggleMode.HELP:
            print(HELP_MESSAGE)
            return 0
        case ToggleMode.STATUS:
            print_libvirt_status()
            return 0
        case ToggleMode.ON:
            return enable_libvirt_daemons()
        case ToggleMode.OFF:
            return disable_libvirt_daemons()


def main() -> int:
    """Handle the arguments and run the script."""
    try:
        mode = parse_basic_toggle_args(
            prompt="Would you like libvirt modular daemons to be enabled?"
        )
    except CommandUsageError as e:
        print(f"Usage error: {e}. See usage with --help.")
        return 2

    return run(mode)


if __name__ == "__main__":
    sys.exit(main())
