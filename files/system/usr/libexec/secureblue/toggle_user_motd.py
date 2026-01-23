#!/usr/bin/python3
#
# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Toggle display of the user-motd in terminal
"""

import os
import sys
from pathlib import Path


# Extra parentheses added so python doesn't check the individual string instead of the path
def main() -> int:
    try:
        os.remove(Path.home() / ".config" / "no-show-user-motd")
        print("MOTD enabled.")

    except FileNotFoundError:
        if not (Path.home() / ".config").is_dir():
            os.mkdir(Path.home() / ".config")
        (Path.home() / ".config" / "no-show-user-motd").touch(exist_ok=False)
        print("MOTD disabled.")

    except OSError as e:
        print(f"ERROR:{e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
