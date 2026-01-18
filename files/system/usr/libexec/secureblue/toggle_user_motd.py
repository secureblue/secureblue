#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Toggle display of the user-motd in terminal
"""

from pathlib import Path
import os

# Extra parentheses added so python doesn't check the individual string instead of the path
def main():
    try:
        os.remove(Path.home() / ".config" / "no-show-user-motd")
        print("MOTD enabled.")

    except FileNotFoundError:
        if (Path.home() / ".config").is_dir() != True:
            os.mkdir(Path.home() / ".config")
        (Path.home() / ".config" / "no-show-user-motd").touch(exist_ok=False)
        print("MOTD disabled.")



if __name__ == "__main__":
     main()
