#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Toggles MAC address randomisation
"""

import os
import sys
from pathlib import Path

RAND_MAC_FILE="/etc/NetworkManager/conf.d/rand_mac.conf"

if RAND_MAC_FILE.exists():

    os.remove(RAND_MAC_FILE)
    print("MAC randomization disabled")

    # bounce the connection to refresh MAC address with host

    connection_profile_name = subprocess.run(["nmcli", "-t", "-f", "NAME,DEVICE", "connection", "show", "--active"], capture_output = True, text = True).stdout.strip().splitlines()
    # check if there is wifi
    for line in connection_profile_name:
        name, device = line.split(':', 1)
        if device == "lo": continue
        connection_profile_name = connection_profile_name.split(':')[0] # The output of the above contains excess data, which can be removed by only taking the part of the string before the first ':'
        subprocess.run(["nmcli", "connection", "down", connection_profile_name])
        subprocess.run(["nmcli", "connection", "up", connection_profile_name])

else:

    print("MAC randomization can be stable (persisting the same random MAC per access point across disconnects/reboots),")
    print("or it can be randomized per-connection (every time it connects to the same access point it uses a new MAC).")

    randomization_choice = input("Do you want to use per-connection Wi-Fi MAC address randomization? [y/N] ")

    if randomization_choice in "Yy":
        randomization_level = "random"
        print("Selected state: per-connection")
    else:
        randomization_level = "stable"
        print("Selected state: per-network (stable)")

    with open(RAND_MAC_FILE, 'w') as f:
        f.write(
            "[device-mac-randomization]\n"
            # "yes" is already the default for scanning
            "wifi.scan-rand-mac-address=yes\n\n"
            "[connection-mac-randomization]\n"
            # Generate a random MAC for each Network and associate the two permanently.
            "ethernet.cloned-mac-address=stable\n"
            "wifi.cloned-mac-address=" + randomization_level + '\n'
            )

    os.chmod(RAND_MAC_FILE, 0o644)
    print("MAC randomization enabled.")

    # bounce the connection

    connection_profile_name = subprocess.run(["nmcli", "-t", "-f", "NAME,DEVICE", "connection", "show", "--active"]).stdout.strip()
    # check if there is wifi
    if connection_profile_name == "lo:lo":
        pass
    else:
        connection_profile_name = connection_profile_name.split(':')[0] # The output of the above contains excess data, which can be removed by only taking the part of the string before the first ':'
        subprocess.run(["nmcli", "connection", "down", connection_profile_name])
        subprocess.run(["nmcli", "connection", "up", connection_profile_name])



