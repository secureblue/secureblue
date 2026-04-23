#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Create or delete a stampfile.
"""

import enum
import sys
from pathlib import Path


class Mode(enum.StrEnum):
    """Enum representing 'create' or 'delete'."""

    CREATE = "create"
    DELETE = "delete"


def set_stampfile(mode: Mode, stampfile_path: str) -> int:
    """Enable or disable an SELinux module."""
    match mode:
        case Mode.CREATE:
            stampfile = Path(stampfile_path)
            stampfile.parent.mkdir(parents=True, exist_ok=True)
            stampfile.touch()
            Path(stampfile_path).touch()
        case Mode.DELETE:
            Path(stampfile_path).unlink(missing_ok=True)
        case _:
            print(f"No such mode: {mode}")
            return 1
    return 0


def main() -> int:
    """Main script entry point."""
    required_args_count = 3
    if len(sys.argv) != required_args_count:
        print("set_stampfile.py must have exactly two arguments.")
        return 2

    try:
        mode = Mode(sys.argv[1])
    except ValueError:
        print("Invalid argument: first argument must be 'create' or 'delete'.")
        return 2

    stampfile_path = sys.argv[2]
    return set_stampfile(mode, stampfile_path)


if __name__ == "__main__":
    sys.exit(main())
