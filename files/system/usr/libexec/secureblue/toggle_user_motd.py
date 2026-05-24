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

from utils import get_config_dir


# Extra parentheses added so python doesn't check the individual string instead of the path
def main() -> int:
    config_dir = get_config_dir()
    no_show_path = config_dir / "no-show-user-motd"

    try:
        os.remove(no_show_path)
        print("MOTD enabled.")

    except FileNotFoundError:
        no_show_path.touch(exist_ok=False)
        print("MOTD disabled.")

    except OSError as e:
        print(f"ERROR:{e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
