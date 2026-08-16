#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
DBus-activated daemon for secureblue-priv-cmd command-line program. Allows
unprivileged users to invoke various commands as root.
"""

import asyncio
import fcntl
import os
import pty
import struct
import subprocess
import termios
from dataclasses import dataclass
from typing import Annotated, Final

from dbus_fast import BusType
from dbus_fast.aio import MessageBus
from dbus_fast.service import ServiceInterface
from dbus_fast.service import method as dbus_method
from dbus_fast.service import signal as dbus_signal


# Shim for older versions of dbus-fast. When newer dbus-fast version is in
# stable Fedora repos, we can replace this with:
# from dbus_fast.annotations import DBusSignature
@dataclass(frozen=True, slots=True)
class DBusSignature:
    signature: str


# Reminder: change these to `tuple[int, int]` when a newer dbus-fast version is
# available in the stable Fedora repos.
uh: Final = Annotated[list[int], DBusSignature("uh")]
uy: Final = Annotated[list[int], DBusSignature("uy")]


class PrivCmdInterface(ServiceInterface):
    _bus: MessageBus
    _background_tasks: set[asyncio.Task]
    _idle_counter: int
    _idle_monitor_task: asyncio.Task | None

    def __init__(self, bus: MessageBus, *, idle_timeout_secs: int | None = None):
        super().__init__("dev.secureblue.PrivCmd0")
        self._bus = bus
        self._background_tasks = set()
        self._idle_counter = 0
        self._idle_monitor_task = None
        if idle_timeout_secs is not None:
            max_idle_count = idle_timeout_secs / 10
            self._idle_monitor_task = asyncio.create_task(self._idle_monitor(10, max_idle_count))

    def _run_command(self, *args: str) -> tuple[int, int]:
        """Run command in pty."""
        cmdline = " ".join(args)
        print(f"Command requested: {cmdline}")
        self._idle_counter = 0
        (m, s) = pty.openpty()
        # Set pty dimensions to 24 rows, 80 columns
        fcntl.ioctl(m, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
        proc = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=s, stderr=s, close_fds=True)
        print(f"PID {proc.pid}: Running command: {cmdline}")
        task = asyncio.create_task(self._signal_exit_code(proc, s))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return (proc.pid, m)

    @dbus_method()
    def BootcStatus(self) -> "uh":
        """Display bootc status."""
        return list(self._run_command("/usr/bin/bootc", "status"))

    @dbus_method()
    def BootcUpgrade(self) -> "uh":
        """Run bootc upgrade."""
        return list(self._run_command("/usr/bin/bootc", "upgrade"))

    @dbus_method()
    def BootcUpgradeCheck(self) -> "uh":
        """Run bootc upgrade --check."""
        return list(self._run_command("/usr/bin/bootc", "upgrade", "--check"))

    @dbus_method()
    def SemoduleList(self) -> "uh":
        """List enabled SELinux modules"""
        return list(self._run_command("/usr/bin/semodule", "-l"))

    @dbus_signal()
    def ChildExited(self, pid: int, exit_code: int) -> "uy":
        return [pid, min(exit_code, 255)]

    async def _signal_exit_code(self, proc: subprocess.Popen, pts: int) -> None:
        proc.wait()
        self.ChildExited(proc.pid, proc.returncode)
        os.close(pts)
        print(f"PID {proc.pid}: Child process exited with code {proc.returncode}")

    async def _idle_monitor(self, freq_secs: float, exit_at_counter: float) -> None:
        while self._idle_counter < exit_at_counter:
            await asyncio.sleep(freq_secs)
            if self._background_tasks:
                self._idle_counter = 0
            else:
                self._idle_counter += 1
        print("Daemon exiting due to idleness.")
        self._bus.disconnect()


async def main() -> None:
    bus = await MessageBus(bus_type=BusType.SYSTEM, negotiate_unix_fd=True).connect()
    interface = PrivCmdInterface(bus, idle_timeout_secs=300)
    bus.export("/dev/secureblue/PrivCmd0", interface)
    await bus.request_name("dev.secureblue.PrivCmd0")
    print("Serving at DBus name dev.secureblue.PrivCmd0")
    await bus.wait_for_disconnect()


if __name__ == "__main__":
    asyncio.run(main())
