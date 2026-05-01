#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 Commenter25
#
# SPDX-License-Identifier: Apache-2.0

"""Actions to take upon the default setting in block-record."""

from . import CONFIG, ResultTuple, is_tty, print_tty
from .mode import ModeArg, mode_ask, mode_parse
from .pipewire import write_pipewire_config


def print_exceptions() -> None:
    """If interactive, displays the apps which differ from the current default."""
    if not is_tty:
        return
    apps = CONFIG.blocked if CONFIG.block_by_default else CONFIG.allowed
    if len(apps) != 0:
        print("With the following exception(s):")
        for app in apps:
            print("\t" + app)


def check(*, show_exceptions: bool = True) -> bool:
    """Prints the current default, and returns it as a boolean."""
    is_blocked = CONFIG.block_by_default
    print_tty(
        "Flatpaks are currently blocked from recording audio by default."
        if is_blocked
        else "Flatpaks are currently allowed to record audio by default."
    )
    if show_exceptions:
        print_exceptions()
    return is_blocked


def modify(wants_block: bool) -> bool:
    """
    Changes whether apps are blocked from recording by default.
    Returns True if setting changed, or False if no change.
    """
    if CONFIG.block_by_default == wants_block:
        print_tty("No change.")
        return False

    CONFIG.block_by_default = wants_block
    CONFIG.write()
    write_pipewire_config()

    print_tty(
        "Flatpaks can no longer record audio by default."
        if CONFIG.block_by_default
        else "Flatpaks may now record audio by default."
    )
    print_exceptions()
    return True


def flow(mode: ModeArg | bool) -> ResultTuple:
    """Flow of execution for changing the default."""
    is_blocked = check()
    if mode is None:
        mode = mode_ask()
    wants_block = mode_parse(mode, is_blocked)
    changed = modify(wants_block)
    return (wants_block, changed)
