#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Toggles MAC address randomisation
"""

import os

RAND_MAC_FILE="/etc/NetworkManager/conf.d/rand_mac.conf"

if RAND_MAC_FILE.exists():

    os.remove(RAND_MAC_FILE)
    print("MAC randomization disabled")

    # bounce the connection to refresh MAC address with host

    active_connections = subprocess.run(["nmcli", "-t", "-f", "NAME,DEVICE,TYPE", "connection", "show", "--active"], capture_output = True, text = True).stdout.strip().splitlines()
    # check if there is wifi
    # handle multiple connections
    for connection in active_connections:

        try:
            name, device, con_type = connection.split(':', 2)
        except ValueError:
            continue # skipping malformed lines

        if con_type != "wifi": continue # dont disconnect from ethernet needlessly
        if device == "lo": continue

        subprocess.run(["nmcli", "connection", "down", name], check = True)
        subprocess.run(["nmcli", "connection", "up", name], check = True)

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

    # bounce the connection to refresh MAC address with host

    active_connections = subprocess.run(["nmcli", "-t", "-f", "NAME,DEVICE,TYPE", "connection", "show", "--active"], capture_output = True, text = True).stdout.strip().splitlines()
    # check if there is wifi
    # handle multiple connections
    for connection in active_connections:

        try:
            name, device, con_type = connection.split(':', 2)
        except ValueError:
            continue # skipping malformed lines

        if con_type != "wifi": continue # dont disconnect from ethernet needlessly
        if device == "lo": continue

        subprocess.run(["nmcli", "connection", "down", name], check = True)
        subprocess.run(["nmcli", "connection", "up", name], check = True)
