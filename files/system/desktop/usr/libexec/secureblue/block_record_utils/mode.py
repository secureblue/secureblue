#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 Commenter25
#
# SPDX-License-Identifier: Apache-2.0

"""Functionality related to the mode argument of block-record."""

from typing import Literal, overload

from utils import BOLD, RESET, ask_option, print_dedent

from . import ModeArgStrings, is_tty

ModeArg = ModeArgStrings | None
"""The possible values for --mode: allow, block, toggle, or None."""


def mode_parse(mode: ModeArg | bool, explicit_state: bool | None = None) -> bool:
    if mode in ("block", True):
        return True
    if mode in ("allow", False):
        return False
    if mode == "toggle":
        return not explicit_state or True
    return True


@overload
def mode_ask(*, allow_reset: None = None) -> bool | None: ...


@overload
def mode_ask(*, allow_reset: bool) -> bool | Literal["reset"] | None: ...


def mode_ask(*, allow_reset: bool | None = None) -> bool | Literal["reset"] | None:
    if not is_tty:
        return None
    allow_num = 1
    block_num = 2
    print_dedent(f"""
        What would you like to change this to? (Ctrl+C to cancel)
        {BOLD}{allow_num}. Allow:{RESET} Can listen to all input and output streams, including other apps.
        {BOLD}{block_num}. Block:{RESET} Can only play sound, and has no microphone access.
    """)
    if allow_reset is not True:
        return bool(ask_option(2) == block_num)

    reset_num = 3
    print(
        f"{BOLD}{reset_num}. Reset:{RESET} Remove any explicit setting, making this app follow the default."
    )
    result = ask_option(3)
    if result == reset_num:
        return "reset"
    return bool(result == block_num)
