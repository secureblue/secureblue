#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import sys
from pathlib import Path


def enable_gnome_jit() -> None:
    Path("/etc/profile.d/gnome-disable-jit.sh").unlink(missing_ok=True)


def disable_gnome_jit() -> None:
    Path("/usr/etc/profile.d/gnome-disable-jit.sh").copy_into(
        "/etc/profile.d", preserve_metadata=True
    )


def main() -> int:
    required_args_count: int = 2
    if len(sys.argv) != required_args_count:
        return 1

    mode = sys.argv[1].casefold()
    match mode:
        case "on":
            enable_gnome_jit()
        case "off":
            disable_gnome_jit()
        case _:
            print("Please provide a valid argument (on/off).")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
