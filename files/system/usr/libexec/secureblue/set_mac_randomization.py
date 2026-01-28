#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Toggles MAC address randomisation
"""

import os
import subprocess
from pathlib import Path

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


def disable_randomization():

    os.remove(RAND_MAC_FILE)
    print("MAC randomization disabled")
    rebounce_connection()
    exit()


def set_stable():
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


def set_random():
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



