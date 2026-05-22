#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 Commenter25
#
# SPDX-License-Identifier: Apache-2.0

"""Actions to take upon individual applications in block-record."""

from . import CONFIG, ArgNamespace, ResultTuple, print_tty
from .default import check as default_check
from .mode import ModeArg, mode_ask, mode_parse
from .pipewire import write_pipewire_config


def reset(app_id: str) -> ResultTuple:
    """Removes any explicit configuration for an app."""
    was_blocked = app_id in CONFIG.blocked
    was_allowed = app_id in CONFIG.allowed

    if was_blocked:
        CONFIG.blocked.remove(app_id)
    if was_allowed:
        CONFIG.allowed.remove(app_id)
    CONFIG.write()

    now_blocked = was_allowed and CONFIG.block_by_default
    now_allowed = was_blocked and not CONFIG.block_by_default
    should_write = now_blocked or now_allowed
    if should_write:
        write_pipewire_config()

    print_tty(f"{app_id} is now following the default setting.")
    return (default_check(show_exceptions=False), should_write)


def check(app_id: str) -> tuple[bool, bool]:
    """
    Checks and prints the current state for the app.
    Returns a tuple containing:
        - whether the app is *explicitly* blocked
        - whether the app is blocked at all
    """
    is_blocked = app_id in CONFIG.blocked
    is_allowed = app_id in CONFIG.allowed
    implicit_blocked = CONFIG.block_by_default and not is_allowed

    if is_blocked:
        line = "{0} is explicitly blocked from recording audio."
    elif is_allowed:
        line = "{0} is explicitly allowed to record audio."
    elif implicit_blocked:
        line = "{0} is implicitly blocked from recording audio."
    else:
        line = "{0} is implicitly allowed to record audio."

    print_tty(line.format(app_id))
    return (is_blocked, is_blocked or implicit_blocked)


def modify(wants_block: bool, app_id: str) -> bool:
    """
    Changes whether an app is allowed or blocked from recording.
    Returns True if setting changed, or False if no change.
    """
    should_block = app_id not in CONFIG.blocked and wants_block
    should_allow = app_id not in CONFIG.allowed and not wants_block

    if not (should_block or should_allow):
        print_tty("No change.")
        return False

    def change_list_if(
        condition: bool,
        wanted: list[str],
        remove_from: list[str],
        should_write_if: bool,
        line: str,
    ) -> None:
        if not condition:
            return
        wanted.append(app_id)
        if app_id in remove_from:
            remove_from.remove(app_id)
        if should_write_if:
            write_pipewire_config()
        print_tty(line.format(app_id))

    change_list_if(
        should_block,
        CONFIG.blocked,
        CONFIG.allowed,
        (not CONFIG.block_by_default),
        "{0} is now explicitly blocked from recording audio.",
    )
    change_list_if(
        should_allow,
        CONFIG.allowed,
        CONFIG.blocked,
        (CONFIG.block_by_default),
        "{0} is now explicitly allowed to record audio.",
    )
    CONFIG.write()

    return True


def _modify_flow(mode: ModeArg | bool, app_id: str) -> ResultTuple:
    """Flow of execution for changing an app's override."""
    is_blocked = check(app_id)[0]

    if mode is None:
        mode_or_reset = mode_ask(allow_reset=True)
        if mode_or_reset == "reset":
            return reset(app_id)
        mode = mode_or_reset

    wants_block = mode_parse(mode, is_blocked)
    changed = modify(wants_block, app_id)
    return (wants_block, changed)


def flow(app_id: str, args: ArgNamespace) -> ResultTuple:
    if args.check:
        return (check(app_id)[1], False)
    if args.reset:
        return reset(app_id)
    return _modify_flow(args.mode, app_id)
