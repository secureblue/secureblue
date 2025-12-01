#!/usr/bin/python3

# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Various utility functions used in secureblue scripts.
"""

import subprocess  # nosec
import sys
import textwrap
from collections.abc import Iterable

import rpm


def print_wrapped(text: str, *, width: int = 70) -> None:
    """Print text to stdout, wrapped to the given width."""
    print(textwrap.fill(" ".join(text.split()), width=width))


def print_err(text: str) -> None:
    """Print text to stderr in bold and red."""
    print(f"\x1b[1m\x1b[31m{text}\x1b[0m", file=sys.stderr)


def command_stdout(*args: str, check: bool = True) -> str:
    """Run a command in the shell and return the contents of stdout."""
    # We only call this with trusted inputs and do not set shell=True.
    # nosemgrep: dangerous-subprocess-use-audit
    return subprocess.run(args, capture_output=True, check=check, text=True).stdout.strip()  # nosec


def command_succeeds(*args: str) -> bool:
    """Run a command in the shell and return whether it completes with return code 0."""
    # We only call this with trusted inputs and do not set shell=True.
    # nosemgrep: dangerous-subprocess-use-audit
    return subprocess.run(args, capture_output=True, check=False).returncode == 0  # nosec


def parse_config(
    stream: Iterable[str], *, sep: str = "=", comment: str = "#", section_start: str = "["
) -> dict[str, str]:
    """
    Parse a text stream as a simple configuration file with keys and values separated
    by the given separator ("=" by default).
    """
    config = {}
    for raw_line in stream:
        line = raw_line.strip()
        if sep not in line or line.startswith((comment, section_start)):
            continue
        key, value = line.split(sep, maxsplit=1)
        config[key.strip()] = value.strip()
    return config


def is_rpm_package_installed(name: str) -> bool:
    """Checks if the given RPM package is installed."""
    ts = rpm.TransactionSet()
    matches = ts.dbMatch("name", name)
    return len(matches) > 0


def is_using_vpn() -> bool:
    """Returns whether an OpenVPN or Wireguard VPN is currently in use."""

    # Check for Wireguard VPN use.
    wg_out = command_stdout("/usr/bin/ip", "link", "show", "type", "wireguard")
    if wg_out:
        return True

    # For OpenVPN, we need to figure out whether the default route is via a TUN/TAP interface.
    # Otherwise, we'd detect virtual networks, etc.
    has_openvpn = False
    route_out = command_stdout("/usr/bin/ip", "route", "show", "default")
    tuntap_out = command_stdout("/usr/bin/ip", "tuntap", "list")
    for tuntap in tuntap_out.splitlines():
        # `ip tuntap list` has each interface on its own line, as "dev0: info1 info2 ...".
        tuntap_interface = tuntap.split(":", maxsplit=1)[0]
        if f"dev {tuntap_interface}" in route_out:
            has_openvpn = True
            break

    return has_openvpn


def interruptible_ask(prompt: str) -> str:
    """Ask for a string input, strip whitespace, and exit gracefully if interrupted."""
    prompt = " ".join(prompt.split())
    prompt = "\n" + textwrap.fill(prompt) + " "
    try:
        return input(prompt).strip()
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(130)


def ask_yes_no(prompt: str) -> bool:
    """Returns the user's preference between yes/y (True) and no/n (False)."""
    while True:
        match interruptible_ask(prompt + " [y/n] ").casefold():
            case "y" | "yes":
                return True
            case "n" | "no":
                return False
            case _:
                print("Please enter y (yes) or n (no).")


def ask_option(options_count: int) -> int:
    """Returns the user's chosen number between 1 and options_count."""

    while True:
        raw_option = interruptible_ask(f"Choose an option [1-{options_count}]: ")
        if raw_option.isdigit():
            option = int(raw_option)
            if 1 <= option <= options_count:
                print()
                return option
        print(f"Please enter a number between 1 and {options_count}.")
