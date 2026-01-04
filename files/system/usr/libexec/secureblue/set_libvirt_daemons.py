#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
# SPDX-License-Identifier: Apache-2.0

"""Enable, disable, or check status of libvirt daemons."""

import enum
import subprocess  # nosec
import sys
from typing import Final

from utils import command_stdout, print_wrapped

HELP_MESSAGE: Final[str] = """\
Toggles if libvirt daemons are enabled. For further documentation, see:
    https://libvirt.org/daemons.html

usage:
ujust set-libvirt-daemons
    Interactively toggle libvirt modular daemons.

ujust set-libvirt-daemons on
    Enable and start all libvirt modular daemons.

ujust set-libvirt-daemons off
    Disable and stop all libvirt modular daemons.

ujust set-libvirt-daemons status
    Show status of libvirt modular daemons.

ujust set-libvirt-daemons --help
    Prints this message.
"""


def _systemd_units_status(*units: str) -> list[str]:
    """Get systemd unit status."""
    output = command_stdout("/usr/bin/systemctl", "is-enabled", "--", *units, check=False)
    return output.splitlines()


def enable_systemd_units(*units: str, start: bool = True) -> int:
    """Enable a list of systemd units."""
    now = ("--now",) if start else ()
    result = subprocess.run(["/usr/bin/systemctl", "enable", *now, "--", *units], check=False)  # nosec
    return result.returncode


def disable_systemd_units(*units: str, stop: bool = True) -> int:
    """Disable a list of systemd units."""
    now = ("--now",) if stop else ()
    result = subprocess.run(["/usr/bin/systemctl", "disable", *now, "--", *units], check=False)  # nosec
    return result.returncode


class LibvirtDaemonSelection(enum.Flag):
    """Selection of libvirt daemons to enable or disable."""

    QEMUD = enum.auto()
    INTERFACED = enum.auto()
    NETWORKD = enum.auto()
    NODEDEVD = enum.auto()
    NWFILTERD = enum.auto()
    SECRETD = enum.auto()
    STORAGED = enum.auto()
    LOGD = enum.auto()
    LOCKD = enum.auto()
    PROXYD = enum.auto()

    @classmethod
    def current_status(cls) -> "LibvirtDaemonSelection":
        """Get current daemon status."""
        sockets = (~cls(0)).sockets()
        status_list = _systemd_units_status(*sockets)
        current = LibvirtDaemonSelection(0)
        for socket, status in zip(cls, status_list, strict=True):
            if status == "enabled":
                current |= socket
        return current

    def daemons(self) -> list[str]:
        """Get list of daemons associated with selection."""
        return ["virt" + daemon.name.lower() for daemon in self if daemon.name is not None]

    def services(self) -> list[str]:
        """Get service units associated with selection."""
        return [f"{daemon}.service" for daemon in self.daemons()]

    def sockets(self) -> list[str]:
        """Get main sockets associated with selection."""
        return [f"{daemon}.socket" for daemon in self.daemons()]

    def sockets_ro(self) -> list[str]:
        """Get main sockets associated with selection."""
        # virtlogd and virtlockd don't have *-ro.socket
        sockets_ro_mask = ~(self.__class__.LOGD | self.__class__.LOCKD)
        return [f"{daemon}-ro.socket" for daemon in (self & sockets_ro_mask).daemons()]

    def sockets_admin(self) -> list[str]:
        """Get main sockets associated with selection."""
        return [f"{daemon}-admin.socket" for daemon in self.daemons()]

    def enabled_units(self) -> list[str]:
        """Get units that would be enabled with this selection."""
        return (
            # The daemon service units other than virtqemud can be activated on demand
            # by the corresponding sockets, so they don't need to be enabled.
            (self & self.__class__.QEMUD).services()
            + self.sockets()
            + self.sockets_ro()
            + self.sockets_admin()
        )

    def disabled_units(self) -> list[str]:
        """Get units that would be disabled with this selection."""
        return (
            (~self).services() + (~self).sockets() + (~self).sockets_ro() + (~self).sockets_admin()
        )


def enable_all() -> int:
    """Enable and start all libvirt modular daemons."""
    units_to_enable = (~LibvirtDaemonSelection(0)).enabled_units()
    return enable_systemd_units(*units_to_enable, start=True)


def disable_all() -> int:
    """Disable and stop all libvirt modular daemons."""
    units_to_disable = LibvirtDaemonSelection(0).disabled_units()
    return disable_systemd_units(*units_to_disable, stop=True)


def show_status() -> None:
    """Print current libvirt daemon status."""
    current = LibvirtDaemonSelection.current_status()
    enabled = ", ".join(current.daemons()) if current else "(none)"
    disabled = ", ".join((~current).daemons()) if ~current else "(none)"
    print_wrapped(f"enabled: {enabled}", width=80)
    print_wrapped(f"disabled: {disabled}", width=80)


def get_selection(current: LibvirtDaemonSelection) -> LibvirtDaemonSelection | None:
    """Get user's selection of libvirt daemons, given current status."""
    # This import is slow, so put it inside the function so it's only loaded if needed.
    import inquirer  # noqa: PLC0415

    all_daemons = (~LibvirtDaemonSelection(0)).daemons()
    questions = [
        inquirer.Checkbox(
            "daemons",
            message="Select libvirt daemons to enable or disable",
            choices=all_daemons,
            default=current.daemons(),
            carousel=True,
        )
    ]
    answers = inquirer.prompt(questions)
    if answers is None:
        return None

    selection = LibvirtDaemonSelection(0)
    for daemon in LibvirtDaemonSelection:
        if daemon.daemons()[0] in answers["daemons"]:
            selection |= daemon

    return selection


def toggle() -> int:
    """Toggle libvirt modular daemons interactively."""
    current = LibvirtDaemonSelection.current_status()
    selected = get_selection(current)

    if selected is None:
        return 0

    if selected == current:
        print("Selection unchanged.")
        return 0

    ret = 0

    newly_enabled = selected & ~current
    if newly_enabled:
        ret = enable_systemd_units(*newly_enabled.enabled_units(), start=True)
        if ret != 0:
            return ret

    newly_disabled = current & ~selected
    if newly_disabled:
        ret = disable_systemd_units(*(~newly_disabled).disabled_units(), stop=True)

    return ret


def main() -> int:
    """Handle the arguments and run the script."""
    mode = sys.argv[1].casefold() if len(sys.argv) > 1 else None
    match mode:
        case "help" | "-h" | "--help":
            print(HELP_MESSAGE)
            return 0
        case "on":
            return enable_all()
        case "off":
            return disable_all()
        case "status":
            show_status()
            return 0
        case None:
            return toggle()
        case _:
            print("Invalid argument. See usage with --help.", file=sys.stderr)
            return 2


if __name__ == "__main__":
    sys.exit(main())
