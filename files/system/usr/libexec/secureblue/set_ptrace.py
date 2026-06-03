#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Configure ptrace support (for anticheat, debugging tools, etc.)"""

import subprocess
import sys
from typing import Final, assert_never

from utils import get_selinux_booleans, set_selinux_booleans
from utils.ptrace import (
    SEBOOL_CONTAINER_ALLOW_PTRACE,
    SEBOOL_DENY_PTRACE,
    YAMA_DOC_URL,
    PtraceStatus,
    get_ptrace_status,
)

HELP_MESSAGE: Final[str] = """\
Configure ptrace support (for anticheat, debugging tools, etc.)

usage:
ujust set-ptrace
    Configure ptrace support interactively.

ujust set-ptrace on
    Enable restricted ptrace: all processes can ptrace their child processes.

ujust set-ptrace container
    Enable restricted ptrace inside the container domain only.

ujust set-ptrace off
    Disable ptrace.

ujust set-ptrace --help
    Prints this message.
"""


def show_status() -> None:
    """Show current ptrace status."""
    match get_ptrace_status():
        case PtraceStatus.DISABLED:
            print("ptrace is disabled")
        case PtraceStatus.ADMIN_ONLY:
            print("ptrace is available only to administrative users")
        case PtraceStatus.CONTAINER_ONLY:
            print("Restricted ptrace is enabled inside containers only")
        case PtraceStatus.RESTRICTED:
            print("Restricted ptrace is enabled")
        case PtraceStatus.UNRESTRICTED:
            print("WARNING: Unrestricted ptrace is enabled!")
        case _ as unreachable:
            assert_never(unreachable)


def get_selection() -> str | None:
    """Get user's selection of libvirt daemons, given current status."""
    # This import is slow, so put it inside the function so it's only loaded if needed.
    import inquirer  # noqa: PLC0415

    print("(up/down to navigate, enter to confirm, Ctrl+C to cancel)")
    try:
        choice = inquirer.list_input(
            "Set ptrace status", choices=["enabled", "container-only", "disabled"], carousel=True
        )
    except KeyboardInterrupt:
        print("[canceled by user]")
        return None
    match choice:
        case "enabled":
            return "on"
        case "container-only":
            return "container"
        case "disabled":
            return "off"
        case _:
            raise ValueError("invalid selection")


def check_ptrace_scope() -> None:
    """Check for unexpected ptrace_scope values."""
    with open("/proc/sys/kernel/yama/ptrace_scope", encoding="utf-8") as f:
        ptrace_scope = int(f.read())
    match ptrace_scope:
        case 0:
            print("WARNING: ptrace is unrestricted (kernel.yama.ptrace_scope = 0)")
            print(YAMA_DOC_URL)
        case 1:
            pass
        case 2:
            print("Additional ptrace restrictions are configured (possibly in /etc/sysctl.d):")
            print("kernel.yama.ptrace_scope is set to 2.")
            print("NOTE: This restricts the use of ptrace to administrative users only.")
            print(YAMA_DOC_URL)
        case 3:
            print("Additional ptrace restrictions are configured (possibly in /etc/sysctl.d):")
            print("kernel.yama.ptrace_scope is set to 3.")
            print("NOTE: This completely forbids the use of ptrace system-wide.")
            print(YAMA_DOC_URL)
        case _:
            raise ValueError(f"invalid value '{ptrace_scope}' for ptrace_scope")


def enable_ptrace() -> int:
    """Enable (restricted) ptrace access."""
    check_ptrace_scope()

    if SEBOOL_DENY_PTRACE not in get_selinux_booleans(SEBOOL_DENY_PTRACE):
        print("ptrace is already allowed by SELinux.")
        return 0

    return set_selinux_booleans({SEBOOL_DENY_PTRACE: False}, permanent=True)


def set_container_ptrace() -> int:
    """Enable (restricted) ptrace access in containers only."""
    check_ptrace_scope()

    sebools = get_selinux_booleans(SEBOOL_DENY_PTRACE, SEBOOL_CONTAINER_ALLOW_PTRACE)
    if SEBOOL_DENY_PTRACE in sebools and SEBOOL_CONTAINER_ALLOW_PTRACE in sebools:
        print("Container-only ptrace is already set.")
        return 0

    return set_selinux_booleans({SEBOOL_DENY_PTRACE: True, SEBOOL_CONTAINER_ALLOW_PTRACE: True})


def disable_ptrace() -> int:
    """Disable ptrace access."""
    check_ptrace_scope()

    sebools = get_selinux_booleans(SEBOOL_DENY_PTRACE, SEBOOL_CONTAINER_ALLOW_PTRACE)
    if SEBOOL_DENY_PTRACE in sebools and SEBOOL_CONTAINER_ALLOW_PTRACE not in sebools:
        print("ptrace is already disabled.")
        return 0

    return set_selinux_booleans({SEBOOL_DENY_PTRACE: True, SEBOOL_CONTAINER_ALLOW_PTRACE: False})


def main() -> int:
    """Handle the arguments and run the script."""
    mode = sys.argv[1].casefold() if len(sys.argv) > 1 else get_selection()
    try:
        match mode:
            case "help" | "-h" | "--help":
                print(HELP_MESSAGE)
                exit_code = 0
            case "status":
                show_status()
                exit_code = 0
            case "on":
                exit_code = enable_ptrace()
            case "container":
                exit_code = set_container_ptrace()
            case "off":
                exit_code = disable_ptrace()
            case None:
                exit_code = 130  # SIGINT
            case _:
                print("Invalid argument. See usage with --help.", file=sys.stderr)
                exit_code = 2
    except subprocess.CalledProcessError:
        exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
