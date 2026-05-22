#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 Commenter25
#
# SPDX-License-Identifier: Apache-2.0

"""Prevent flatpaks from recording audio streams."""

import sys

from block_record_utils import (
    CONFIG,
    create_args,
    default,
    individual,
    is_tty,
    print_err,
    resolve_app_id,
)
from block_record_utils.pipewire import write_pipewire_config


def main() -> int:
    """Main entry point for script."""
    args = create_args()

    app_id = resolve_app_id(args.app_id)
    if app_id is None and (args.app_id is not None):
        print_err("No matching app IDs found; exiting.")
        return 1
    if app_id is None and args.reset:
        print_err("No app ID given.")
        return 1

    CONFIG.load()
    if app_id:
        is_blocked, changed = individual.flow(app_id, args)
    elif args.force and not args.mode:
        # only --force passed, so avoid change, just write pipewire config
        is_blocked = default.check() if args.check else CONFIG.block_by_default
        changed = False
    else:
        is_blocked, changed = default.flow(args.mode)

    if not changed and args.force:
        write_pipewire_config()

    if not is_tty:
        print("block" if is_blocked else "allow")

    return 0


if __name__ == "__main__":
    sys.exit(main())
