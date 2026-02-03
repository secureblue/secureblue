#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Sets MAC address randomisation
"""

import sys
from pathlib import Path
from enum import StrEnum

import inquirer
import sandbox
from utils import (
    CommandUsageError,
    SystemdService,
    print_wrapped
    )

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

class Mode(StrEnum):
    HELP = "HELP"
    INTERACTIVE = "INTERACTIVE"
    STABLE = "STABLE"
    RANDOM = "RANDOM"
    OFF = "OFF"
    STATUS = "STATUS"



def run_restart_networkmanager() -> None:
    """Restarts NetworkManager so the MAC address can be refreshed."""

    # Note: Simply toggling connections is not a substitute.

    return SystemdService("NetworkManager.service").restart()


disable_mac_randomization = sandbox.SandboxedFunction(
    file_name="disable_mac_randomization.py", read_write_paths=["/etc/NetworkManager/conf.d"]
)


def return_status() -> str:
    """Returns the current MAC randomisation status [stable/random/off]"""
    if Path(RAND_MAC_FILE).exists():
        with open(RAND_MAC_FILE, encoding="utf-8") as f:
            for line in f:
                if line.startswith("wifi.cloned-mac-address="):
                    status = line.split("=", 1)[1].strip()
                    print(f"The current status is: {status}")
                    return status
    else:
        print("The current status is: Off")
        return "Off"


def run_disable_randomization() -> int:
    """Runs sandboxed disable_randomization() function."""
    if Path("/etc/NetworkManager/conf.d/rand_mac.conf").exists():
        out = sandbox.run(disable_mac_randomization)
        if not out: # out == 0 means success
            run_restart_networkmanager()
        else:
            print("Failed to disable MAC randomization.")

        return out

    else:
        print(
            "MAC randomization config not found. This usually means MAC randomization was already off."
        )



set_mac_randomization_stable = sandbox.SandboxedFunction(
    file_name="set_mac_randomization_stable.py", read_write_paths=["/etc/NetworkManager/conf.d"]
)


def run_set_randomization_stable() -> int:
    """Runs sandboxed set_mac_randomization_stable function."""
    if return_status() == "stable":
        print("MAC randomization is already set to per-network (stable).")
        return 0

    else:
        out = sandbox.run(set_mac_randomization_stable)
        restart_success = run_restart_networkmanager()
        if not restart_success: # restart_success == 0 if successful
            return out
        else:
            return restart_success # return the fail code


set_mac_randomization_random = sandbox.SandboxedFunction(
    file_name="set_mac_randomization_random.py", read_write_paths=["/etc/NetworkManager/conf.d"]
)


def run_set_randomization_random() -> int:
    """Runs sandboxed set_mac_randomization_random function."""
    if return_status() == "random":
        print("MAC randomization is already set to per-network (random).")
        return 0

    else:
        out = sandbox.run(set_mac_randomization_random)
        run_restart_networkmanager()
        return out


def interactive_selection() -> int:
    """Uses the inquirer module and user input to select an mode via the CLI"""
    questions = [
        inquirer.List(
            "Mode",
            message="Select a mode of MAC randomization",
            choices=["Status", "Per-network", "Per-connection", "Off"],
        ),
    ]
    answer = inquirer.prompt(questions)["Mode"]
    print("Selection: " + answer)
    match answer:
        case "Status":
            return_status()
            return 0

        case "Per-network":
            return run_set_randomization_stable()

        case "Per-connection":
            return run_set_randomization_random()

        case "Off":
            return run_disable_randomization()

        case _:
            raise ValueError(
                "Script malfunction: Prompt returned an unexpected value."
            )  # This line *should* never run


def parse_mode_args() -> strEnum:
    """Parses the argument passed to this script"""
    args = sys.argv[1:]

    if not args:
        return Mode.INTERACTIVE  # User will use inquirer module to select

    if args[0] in ("--help", "-h", "help"):
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


def run(mode: strEnum) -> int:
    """Selects which function to run by referencing the provided mode."""
    print_wrapped(
        "\nWARNING: It is known that MAC randomization breaks network connectivity on some hypervisors (Hyper-V for example)."
    )
    print("") # newline for readability
    match mode:
        case Mode.INTERACTIVE:
            return interactive_selection()

        case Mode.STABLE:
            return run_set_randomization_stable()

        case Mode.RANDOM:
            return run_set_randomization_random()

        case Mode.OFF:
            return run_disable_randomization()

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
