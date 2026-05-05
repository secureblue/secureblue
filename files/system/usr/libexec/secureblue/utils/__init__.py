#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Various utility functions used in secureblue scripts.
"""

import enum
import json
import subprocess
import sys
import textwrap
from collections.abc import Iterable, Sequence

import rpm


class ToggleMode(enum.StrEnum):
    """Valid mode for toggle script: 'on', 'off', 'status', or 'help'."""

    ON = "on"
    OFF = "off"
    STATUS = "status"
    HELP = "help"


class CommandUsageError(Exception):
    """Error in command-line arguments."""


def parse_basic_toggle_args(*, prompt: str | None = None) -> ToggleMode:
    """
    Parse command-line arguments into a ToggleMode. Raises CommandUsageError on invalid arguments.
    """
    argc_interactive = 1
    argc_on_off = 2

    if prompt is not None and len(sys.argv) == argc_interactive:
        # Ask interactively.
        return ToggleMode.ON if ask_yes_no(prompt) else ToggleMode.OFF

    if len(sys.argv) == argc_on_off:
        # Take mode from first argument, i.e. 'on' or 'off'.
        mode = sys.argv[1].casefold()
    else:
        raise CommandUsageError("Too many options specified")

    if mode in ("help", "-h", "--help"):
        return ToggleMode.HELP

    try:
        return ToggleMode(mode)
    except ValueError as e:
        raise CommandUsageError("Invalid option selected") from e


class Image(enum.Enum):
    """Fedora atomic base image"""

    SILVERBLUE = enum.auto()
    KINOITE = enum.auto()
    SERICEA = enum.auto()
    COSMIC = enum.auto()
    COREOS = enum.auto()
    IOT = enum.auto()

    @classmethod
    def from_image_ref(cls, image_ref: str) -> "Image | None":
        """Convert an image reference to the corresponding Image enum instance."""
        image_dict: dict[str, Image] = {
            "silverblue": cls.SILVERBLUE,
            "kinoite": cls.KINOITE,
            "sericea": cls.SERICEA,
            "cosmic": cls.COSMIC,
            "securecore": cls.COREOS,
            "iot": cls.IOT,
        }
        image_name = image_ref.rsplit("/", maxsplit=1)[-1]
        image_prefix = image_name.split("-", maxsplit=1)[0]
        return image_dict.get(image_prefix)

    @classmethod
    def by_alias(cls, alias: str) -> "Image | None":
        """Look up Image enum instance by alias."""
        alias = alias.casefold()
        aliases: dict[Image, Sequence[str]] = {
            cls.SILVERBLUE: ("silverblue", "gnome"),
            cls.KINOITE: ("kinoite", "kde", "plasma"),
            cls.SERICEA: ("sericea", "sway"),
            cls.COSMIC: ("cosmic",),
            cls.COREOS: ("securecore", "coreos"),
            cls.IOT: ("iot",),
        }
        for image, image_aliases in aliases.items():
            if alias in image_aliases:
                return image
        return None

    def is_server(self) -> bool:
        """Is the image a server image?"""
        return self in (Image.COREOS, Image.IOT)

    def is_desktop(self) -> bool:
        """Is the image a desktop image?"""
        return not self.is_server()


def booted_image_ref() -> str:
    """Get the image reference of the booted deployment."""
    ostree_status = command_stdout("/usr/bin/rpm-ostree", "status", "--json")
    image_ref = json.loads(ostree_status)["deployments"][0]["container-image-reference"]
    if not isinstance(image_ref, str):
        raise ValueError("container-image-reference should be a JSON string")
    return image_ref


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
    return subprocess.run(args, capture_output=True, check=check, text=True).stdout.strip()


def command_succeeds(*args: str) -> bool:
    """Run a command in the shell and return whether it completes with return code 0."""
    # We only call this with trusted inputs and do not set shell=True.
    # nosemgrep: dangerous-subprocess-use-audit
    ret_code = subprocess.run(
        args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
    ).returncode
    return ret_code == 0


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


def is_module_loaded(module_name: str) -> bool:
    """Check whether the passed module name is currently loaded"""

    try:
        with open("/proc/modules", encoding="utf8") as fd:
            return any(line.startswith(module_name + " ") for line in fd)
    except OSError:
        return False


def loaded_kernel_modules() -> frozenset[str]:
    """Get the set of currently loaded kernel modules."""
    with open("/proc/modules", encoding="utf8") as f:
        return frozenset(line.split(maxsplit=1)[0] for line in f)


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
