#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Boot into this device's BIOS/UEFI screen."""

from os import path
from subprocess import run

from utils import ask_yes_no

if path.exists("/sys/firmware/efi"):
    if ask_yes_no("The system will reboot into UEFI firmware settings. Proceed?"):
        run(["/usr/bin/systemctl", "reboot", "--firmware-setup"], check=True)
else:
    print("Rebooting to legacy BIOS from OS is not supported.")
