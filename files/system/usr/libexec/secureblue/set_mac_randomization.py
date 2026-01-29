#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Sets MAC address randomisation
"""

import os
import sys
import subprocess
from pathlib import Path

import sandbox
from utils import (
    CommandUsageError
)
import inquirer

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


def rebounce_connection() -> None: # TODO: switch this with a reset NetworkManager function
    """bounces the connection to refresh MAC address with host"""
    active_connections = (
        subprocess.run(
            ["/usr/bin/nmcli", "-t", "-f", "NAME,DEVICE,TYPE", "connection", "show", "--active"],
            capture_output=True,
            text=True,
            check=True,
        )
        .stdout.strip()
        .splitlines()
    )
    # check if there is wifi
    # handle multiple connections
    for connection in active_connections:
        try:
            name, device, con_type = connection.split(":", 2)
        except ValueError:
            continue  # skipping malformed lines
        if device == "lo":
            continue

        subprocess.run(["/usr/bin/nmcli", "connection", "down", name], check=True)
        subprocess.run(["/usr/bin/nmcli", "connection", "up", name], check=True)


disable_mac_randomization = sandbox.SandboxedFunction(
    file_name = "disable_mac_randomization.py",
    read_write_paths = ["/etc/NetworkManager/conf.d"]
    )
def run_disable_randomization() -> int:
    """Runs sandboxed disable_randomization() function."""
    out = sandbox.run(disable_mac_randomization)
    rebounce_connection()
    return out


set_mac_randomization_stable = sandbox.SandboxedFunction(
    file_name = "set_mac_randomization_stable.py",
    read_write_paths = ["/etc/NetworkManager/conf.d"]
    )
def run_set_randomization_stable() -> int:
    """Runs sandboxed set_mac_randomization_stable function."""
    out = sandbox.run(set_mac_randomization_stable)
    rebounce_connection()
    return out


set_mac_randomization_random = sandbox.SandboxedFunction(
    file_name = "set_mac_randomization_random.py",
    read_write_paths = ["/etc/NetworkManager/conf.d"]
    )
def run_set_randomization_random() -> int:
    """Runs sandboxed set_mac_randomization_random function."""
    out = sandbox.run(set_mac_randomization_random)
    rebounce_connection()
    return out


def return_status() -> int:
    """Returns the current MAC randomisation status [stable/random/off]"""
    if Path(RAND_MAC_FILE).exists():
        with open(RAND_MAC_FILE, encoding="utf-8") as f:
            for line in f:
                if line.startswith("wifi.cloned-mac-address="):
                    status = line.strip().split("=", 1)[1]
                    print(f"The current status is: {status}")
    else:
        print("The current status is: Off")

    return 0


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
            return return_status()

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


def parse_mode_args() -> str:
    """Parses the argument passed to this script"""
    args = sys.argv[1:]

    if not args:
        return "INTERACTIVE"  # User will use inquirer module to select

    if args[0] in ("--help", "-h", "help"):
        return "HELP"

    match args[0]:
        case "stable":
            return "STABLE"

        case "random":
            return "RANDOM"

        case "off":
            return "OFF"

        case "status":
            return "STATUS"

        case _:
            raise CommandUsageError(f"Invalid argument value: '{args[0]}'")


def run(mode: str) -> int:
    """Selects which function to run by referencing the provided mode"""
    print(
        "\nWARNING: It is known that set-mac-randomization breaks network connectivity on some hypervisors (Hyper-V for example).\n"
    )
    match mode:
        case "INTERACTIVE":
            return interactive_selection()

        case "STABLE":
            return run_set_randomization_stable()

        case "RANDOM":
            return run_set_randomization_random()

        case "OFF":
            return run_disable_randomization()

        case "STATUS":
            return return_status()

        case "HELP":
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
