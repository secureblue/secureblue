#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Sets MAC address randomization
"""

import sys
from enum import StrEnum
from pathlib import Path
from typing import assert_never

import inquirer
import sandbox
from utils import CommandUsageError, SystemdService, print_wrapped

HELP_MESSAGE = """\
Sets the MAC randomization mode.

usage:
ujust set_mac_randomization
    Sets MAC randomization status interactively based on the user's preference.

ujust set-mac-randomization stable
    Sets MAC randomization to per-network.

ujust set-mac-randomization random
    Sets MAC randomization to per-connection.

ujust set-mac-randomization off
    Disables MAC randomization.

ujust set-mac-randomization status
    Prints the MAC randomization status.

"""

RAND_MAC_FILE = "/etc/NetworkManager/conf.d/rand_mac.conf"

status_string_off = "Off"


class Mode(StrEnum):
    """Predefine randomization selection enums."""

    HELP = "HELP"
    INTERACTIVE = "INTERACTIVE"
    STABLE = "STABLE"
    RANDOM = "RANDOM"
    OFF = "OFF"
    STATUS = "STATUS"


def run_restart_networkmanager() -> int:
    """Restarts NetworkManager so the MAC address can be refreshed."""

    # Note: Simply toggling connections is not a substitute.

    return SystemdService("NetworkManager.service").restart()


def return_status(silent: bool = False) -> str:
    """
    Returns the current randomisation status [stable/random/off]
    and optionally prints it out.
    """

    try:
        with open(RAND_MAC_FILE, encoding="utf-8") as f:
            for line in f:
                if line.startswith("wifi.cloned-mac-address="):
                    value_index = 1
                    status = line.split("=", maxsplit=1)[value_index].strip()
                    if not silent:
                        print(f"The current status is: {status}")
                    return status
    except FileNotFoundError:
        if not silent:
            print("The current status is: Off")
        return status_string_off

    return status_string_off  # File exists but has no contents, defaulting to off.


disable_mac_randomization = sandbox.SandboxedFunction(
    file_name="disable_mac_randomization.py", read_write_paths=["/etc/NetworkManager/conf.d"]
)

set_mac_randomization_stable = sandbox.SandboxedFunction(
    file_name="set_mac_randomization_stable.py", read_write_paths=["/etc/NetworkManager/conf.d"]
)

set_mac_randomization_random = sandbox.SandboxedFunction(
    file_name="set_mac_randomization_random.py", read_write_paths=["/etc/NetworkManager/conf.d"]
)


def set_randomization_state(state: Mode) -> int: #pylint: ignore=C901
    """Sets the mac randomization state (stable, random, off), running the sandboxed functions."""
    sandboxed_function_exitcode = 0

    match state:
        case Mode.OFF:
            # Run sandboxed disable_randomization() function.
            if Path(RAND_MAC_FILE).exists():  # may TOCTOU
                sandboxed_function_exitcode = sandbox.run(disable_mac_randomization)
            else:
                print_wrapped(
                    "MAC randomization config not found. "
                    + "This usually means MAC randomization is already off."
                )
                return 0

        case Mode.STABLE:
            # Run sandboxed set_mac_randomization_stable function.
            print("Selected state: per-network (stable)")

            if return_status(silent=True) == "stable":
                print("MAC randomization is already set to per-network (stable).")
                return 0

            sandboxed_function_exitcode = sandbox.run(set_mac_randomization_stable)

        case Mode.RANDOM:
            # Run sandboxed set_mac_randomization_random function.
            print("Selected state: per-connection (random)")

            if return_status(silent=True) == "random":
                print("MAC randomization is already set to per-network (random).")
                return 0

            sandboxed_function_exitcode = sandbox.run(set_mac_randomization_random)

        case _:
            raise ValueError("Unhandled mode: " + state)

    if sandboxed_function_exitcode:  # sandboxed_function_exitcode != 0 means failure
        print(f"Failed set MAC randomization. Code:{sandboxed_function_exitcode}")
        return 1

    restart_success = run_restart_networkmanager()

    if restart_success != 0:  # 0 == success, not 0 == failure
        print_wrapped(
            "Failed to restart NetworkManager. "
            + "Restart it or this computer for changes to take effect."
        )
        return restart_success  # return the error code


    print(f"MAC randomization set to {state} successfully.")
    return 0


def interactive_selection() -> int:
    """Uses the inquirer module and user input to select an mode via the CLI"""
    questions = [
        inquirer.List(
            "Mode",
            message="Select a mode of MAC randomization",
            choices=["Status", "Per-network (stable)", "Per-connection (random)", "Off"],
        ),
    ]
    answer = inquirer.prompt(questions)["Mode"]
    print("Selection: " + answer)
    match answer:
        case "Status":
            return_status()
            return 0

        case "Per-network (stable)":
            return set_randomization_state(Mode.STABLE)

        case "Per-connection (random)":
            return set_randomization_state(Mode.RANDOM)

        case "Off":
            return set_randomization_state(Mode.OFF)

        case _ as unreachable:
            assert_never(unreachable)


def parse_mode_args() -> StrEnum:
    """Parses the argument passed to this script"""
    args = sys.argv[1:]

    if not args:
        return Mode.INTERACTIVE  # User will use inquirer module to select

    if args[0] in ("--help", "-h", "help", "?") or len(args) != 1:
        return Mode.HELP

    match args[0]:
        case "stable" | "per-network":
            return Mode.STABLE

        case "random" | "per-connection":
            return Mode.RANDOM

        case "off" | "disable":
            return Mode.OFF

        case "status":
            return Mode.STATUS

        case _:
            raise CommandUsageError(f"Invalid argument value: '{args[0]}'")


def run(mode: Mode) -> int:
    """Selects which function to run by referencing the provided mode."""
    print()  # newline for readability
    print_wrapped(
        "WARNING: MAC randomization breaks network connectivity on some hypervisors (e.g. Hyper-V)."
    )
    print()  # newline for readability
    match mode:
        case Mode.INTERACTIVE:
            return interactive_selection()

        case Mode.STABLE:
            return set_randomization_state(mode)

        case Mode.RANDOM:
            return set_randomization_state(mode)

        case Mode.OFF:
            return set_randomization_state(mode)

        case Mode.STATUS:
            return_status()
            return 0

        case Mode.HELP:
            print(HELP_MESSAGE)
            return 0

        case _:
            raise ValueError("Unhandled mode: " + mode)


# -------------------------------- #


def main() -> int:
    """Handle the arguments and run the script."""
    try:
        mode = parse_mode_args()
    except CommandUsageError as e:
        print(f"Usage error: {e}. See usage with --help or --h.")
        return 2

    return run(mode)


if __name__ == "__main__":
    sys.exit(main())
