#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Client-side of secureblue-priv-cmd command-line program. Allows unprivileged
users to invoke various commands as root.
"""

import asyncio
import errno
import sys
from typing import Final

from dbus_fast import BusType, DBusError
from dbus_fast.aio import MessageBus, ProxyInterface
from dbus_fast.introspection import Node

DBUS_NAME: Final[str] = "dev.secureblue.PrivCmd0"
DBUS_PATH: Final[str] = "/dev/secureblue/PrivCmd0"
DBUS_INTERFACE: Final[str] = "dev.secureblue.PrivCmd0"

PROGRAM_NAME: Final[str] = sys.argv[0].rsplit("/", maxsplit=1)[-1]
HELP_MESSAGE: Final[str] = f"""\
Allows unprivileged users to run specific privileged commands as root via a
DBus-activated service.

usage:
{PROGRAM_NAME} bootc-status
    Run `bootc status`.
{PROGRAM_NAME} bootc-upgrade
    Run `bootc upgrade`.
{PROGRAM_NAME} bootc-upgrade-check
    Run `bootc upgrade --check`.
{PROGRAM_NAME} semodule-list
    Run `semodule -l`.
{PROGRAM_NAME} --help
    Print this message.
"""


def print_error(msg: str) -> None:
    print(f"{PROGRAM_NAME}: {msg}", file=sys.stderr)


async def _print_lines(pty_fd: int) -> None:
    with open(pty_fd, encoding="utf8") as pty:
        try:
            for line in pty:
                print(line, end="")
        except OSError as err:
            # EIO ("I/O error") is expected when the other end of the pty is closed
            if err.errno != errno.EIO:
                raise


class CommandHandler:
    child_exited_event: asyncio.Event
    pid: int | None
    exit_code: int | None
    unchecked_exit_codes: dict[int, int]

    def __init__(self) -> None:
        self.child_exited_event = asyncio.Event()
        self.pid = None
        self.exit_code = None
        self.unchecked_exit_codes = {}

    def set_exit_code(self, pid: int, exit_code: int) -> None:
        if self.pid is None:
            self.unchecked_exit_codes[pid] = exit_code
        elif pid == self.pid:
            self.exit_code = exit_code
            self.child_exited_event.set()

    async def call_command(self, interface: ProxyInterface, cmd: str) -> int:
        try:
            method = getattr(interface, f"call_{cmd.replace('-', '_')}")
        except AttributeError:
            print(f"Error: invalid command '{cmd}'")
            return 2

        interface.on_child_exited(self.set_exit_code)  # ty: ignore[unresolved-attribute]
        pid, pty_fd = await method()

        self.pid = pid
        # Handle case where child process exited in the brief window before we
        # received the reply over DBus:
        if pid in self.unchecked_exit_codes:
            self.exit_code = self.unchecked_exit_codes[pid]
            self.unchecked_exit_codes.clear()
            self.child_exited_event.set()

        # Print lines as they're received while waiting for child process exit signal
        async with asyncio.TaskGroup() as tg:
            tg.create_task(_print_lines(pty_fd))
            tg.create_task(self.child_exited_event.wait())

        if self.exit_code is None:
            raise RuntimeError("unreachable")
        return self.exit_code


async def main() -> int:
    arg_count = len(sys.argv) - 1
    if arg_count != 1:
        print_error(f"Expected 1 argument, got {arg_count}. Run with --help option for usage.")
        return 2

    cmd = sys.argv[1].casefold()
    if cmd in ("--help", "help", "-h"):
        print(HELP_MESSAGE)
        return 0

    bus = await MessageBus(bus_type=BusType.SYSTEM, negotiate_unix_fd=True).connect()

    try:
        with open(f"/usr/share/dbus-1/interfaces/{DBUS_INTERFACE}.xml", encoding="utf8") as f:
            introspection_xml = f.read()
    except OSError:
        introspection = await bus.introspect(DBUS_NAME, DBUS_PATH)
    else:
        introspection = Node.parse(introspection_xml)

    proxy = bus.get_proxy_object(DBUS_NAME, DBUS_PATH, introspection)
    interface = proxy.get_interface(DBUS_INTERFACE)
    handler = CommandHandler()
    try:
        return await handler.call_command(interface, cmd)
    except DBusError as err:
        print_error(f"Error: {err}")
        return 1
    finally:
        bus.disconnect()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
