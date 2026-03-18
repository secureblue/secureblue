#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
The sandboxed webcam toggle function
"""

import os
import sys
from typing import Final

WEBCAM_MOD_FILE: Final[str] = "/etc/modprobe.d/99-disable-webcam.conf"
WEBCAM_MOD_TEXT: Final[str] = """install uvcvideo /bin/false"""


def main() -> int:
    """Set or remove the webcam module override"""
    required_args_count = 2
    if len(sys.argv) != required_args_count:
        return 1

    mode = sys.argv[1]
    match mode:
        case "on":
            os.remove(WEBCAM_MOD_FILE)
            print("Webcam has been enabled. Reboot for effect.")
            return 0
        case "off":
            with open(WEBCAM_MOD_FILE, "w", encoding="utf8") as fd:
                fd.write(WEBCAM_MOD_TEXT)
            os.chmod(WEBCAM_MOD_FILE, 0o644)
            print("Webcam has been disabled. Reboot for effect.")
            return 0
        case _:
            print("Invalid inner script argument.")
            return 1


if __name__ == "__main__":
    sys.exit(main())
