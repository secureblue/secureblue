#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Sets MAC address randomisation
"""

import os
import subprocess
from pathlib import Path
import sandbox
from utils import (
    CommandUsageError,
    ToggleMode,
    ask_yes_no,
    command_succeeds,
    parse_basic_toggle_args,
    print_wrapped,
)
from typing import final
import inquirer

HELP_MESSAGE: Final[str] = """\
Sets the MAC randomisation mode.

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


def rebounce_connection(): # bounces the connection to refresh MAC address with host

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

        if con_type != "wifi":
            continue  # dont disconnect from ethernet needlessly
        if device == "lo":
            continue

        subprocess.run(["/usr/bin/nmcli", "connection", "down", name], check=True)
        subprocess.run(["/usr/bin/nmcli", "connection", "up", name], check=True)


def disable_randomization() -> int:

    os.remove(RAND_MAC_FILE)
    print("MAC randomization disabled")
    rebounce_connection()

    return 0


def set_stable() -> int:

    randomization_level = "stable"
    print("Selected state: per-network (stable)")

    with open(RAND_MAC_FILE, "w") as f:
    f.write(
        "[device-mac-randomization]\n"
        # "yes" is already the default for scanning
        "wifi.scan-rand-mac-address=yes\n\n"
        "[connection-mac-randomization]\n"
        # Generate a random MAC for each Network and associate the two permanently.
        "ethernet.cloned-mac-address=stable\n"
        "wifi.cloned-mac-address=" + randomization_level + "\n"
    )

    os.chmod(RAND_MAC_FILE, 0o644)
    print("MAC randomization enabled.")

    rebounce_connection()

    return 0


def set_random() -> int:

    randomization_level = "random"
    print("Selected state: per-connection")

    with open(RAND_MAC_FILE, "w") as f:
    f.write(
        "[device-mac-randomization]\n"
        # "yes" is already the default for scanning
        "wifi.scan-rand-mac-address=yes\n\n"
        "[connection-mac-randomization]\n"
        # Generate a random MAC for each Network and associate the two permanently.
        "ethernet.cloned-mac-address=stable\n"
        "wifi.cloned-mac-address=" + randomization_level + "\n"
    )

    os.chmod(RAND_MAC_FILE, 0o644)
    print("MAC randomization enabled.")

    rebounce_connection()

    return 0


def return_status() -> int:

    with open(RAND_MAC_FILE, "r") as f:
        for line in f:
            if line.startswith("wifi.cloned-mac-address="):
                status = line.strip().split("=",1)[1]
                print(f"The current status is <{status}>")

    print("The current status is <Off>")

    return 0

def interactive_selection() -> int:

    questions = [
    inquirer.List("Mode",
                    message="Select a mode of MAC randomisation",
                    choices=["Status", "Per-network", "Per-connection", "Off"],
                ),
    ]

    match inquirer.prompt(questions):
        case "Status":
            return interactive_selection()

        case "Per-network":
            return set_stable()

        case "Per-connection":
            return set_random()

        case "Off":
            return disable_randomization()

        case _:
            raise ValueError("Script malfunction: Prompt returned an unexpected value.") # This line *should* never run





def parse_mode_args() -> Mode:

    args = sys.argv[1:]

    if not args:
        return Mode.INTERACTIVE # User will use inquirer module to select

    if args[0] in ("--help", "-h"):
        return Mode.HELP

    match args[0]:
        case "stable":
            return Mode.STABLE

        case "random":
            return Mode.RANDOM

        case "off":
            return Mode.OFF

        case "status":
            return Mode.STATUS

        case _:
            raise ValueError(f"Invalid argument value: {args[0]}")


def run(mode: Mode) -> int:
    match mode:
        case Mode.INTERACTIVE:
            return interactive_selection()

        case Mode.STABLE:
            return set_stable()

        case Mode.RANDOM:
            return set_random()

        case Mode.OFF:
            return disable_randomization()

        case Mode.STATUS:
            return return_status()

        case _:
            raise ValueError("Unhandled mode: " + mode)


def main() -> int:
    """Handle the arguments and run the script."""
    try:
        mode = parse_mode_args(
            prompt="This is a test"
        )
    except CommandUsageError as e:
        print(f"Usage error: {e}. See usage with --help.")
        return 2

    return run(mode)


if __name__ == "__main__":
    sys.exit(main())


