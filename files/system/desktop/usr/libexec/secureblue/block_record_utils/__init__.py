#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 Commenter25
#
# SPDX-License-Identifier: Apache-2.0

"""
CLI information and general variables for block-record.

Information specific to secureblue should be kept within this file, and ideally remain static.
Separating it allows easier use outside secureblue, while directly pulling updates for other files.
For example, non-secureblue users will likely change the command name, config path, and imports.
An exception is made for mode.py, which is also CLI information and imports secureblue utils.
"""

from argparse import ArgumentParser
from argparse import Namespace as ArgNamespace
from os import environ
from pathlib import Path
from sys import stdin
from typing import Final, Literal, get_args

# import secureblue utils here so other scripts aren't dependent on secureblue
from flatpak_utils import resolve_app_id as resolve_app_id
from utils import ask_yes_no as ask_yes_no
from utils import print_err as print_err

__all__ = ["ArgNamespace"]

is_tty = stdin.isatty()

XDG_CONFIG_HOME: Final[Path] = Path(environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))

SCRIPT_CONFIG_PATH: Final[Path] = Path(XDG_CONFIG_HOME / "secureblue/ujust-block-record.json")

# everything uses CONFIG, easier to import here, but it needs SCRIPT_CONFIG_PATH and is_tty
from .config import CONFIG as CONFIG  # noqa: E402

PIPEWIRE_CONFIG_PATH: Final[Path] = Path(
    XDG_CONFIG_HOME / "pipewire/pipewire-pulse.conf.d/secureblue-flatpak-rules.conf"
)


COMMAND_NAME: Final[str] = "ujust block-record"

DESCRIPTION: Final[str] = """
Prevent flatpaks from recording audio streams. When called with a
flatpak application ID as an argument, it applies the override to
that application instead of globally.
"""

ModeArgStrings = Literal["allow", "block", "toggle"]


def create_args() -> ArgNamespace:
    parser = ArgumentParser(prog=COMMAND_NAME, description=DESCRIPTION)
    parser.add_argument("app_id", nargs="?", metavar="APP_ID", help="app ID of flatpak to block")
    parser.add_argument(
        "-m", "--mode", choices=get_args(ModeArgStrings), help="asks interactively if unset"
    )
    parser.add_argument(
        "-r", "--reset", action="store_true", help="removes explicit configuration for an app"
    )
    parser.add_argument(
        "-c", "--check", action="store_true", help="no-op, just print the current configuration"
    )
    parser.add_argument("-f", "--force", action="store_true", help="forces PipeWire config update")
    parser.add_argument("-q", "--quiet", action="store_true", help='only print "allow" or "block"')

    args = parser.parse_args()

    if args.quiet:
        global is_tty  # noqa: PLW0603 # sys.stdin.isatty seemingly isn't 100% reliable, -q is a guarantee
        is_tty = False

    return args


def print_tty(line: str) -> None:
    if is_tty:
        print(line)


ResultTuple = tuple[bool, bool]
"""
A tuple for the results at the end of script execution, containing:
    - whether the final result was a block
    - whether the PipeWire config was written to
"""
