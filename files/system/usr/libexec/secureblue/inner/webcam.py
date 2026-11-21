#!/usr/bin/python3 -Es

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
The sandboxed webcam toggle function
"""

import os
import subprocess
import sys
from typing import Final

WEBCAM_KMODS: Final[list[str]] = [
    "ipu-bridge",
    "ipu3-imgu",
    "ipu3-cio2",
    "intel_ipu6",
    "intel_ipu6_isys",
    "intel_ipu7",
    "intel_ipu7_isys",
    "uvcvideo",
]
WEBCAM_MOD_FILE: Final[str] = "/etc/modprobe.d/99-disable-webcam.conf"


def main() -> int:
    """Set or remove the webcam module override"""
    required_args_count = 2
    if len(sys.argv) != required_args_count:
        return 1

    mode = sys.argv[1]
    match mode:
        case "on":
            os.remove(WEBCAM_MOD_FILE)
            # hardware-specific kmods not loaded because there is no way to identify what is needed?
            result = subprocess.run(["/usr/bin/modprobe", "uvcvideo"], check=False)
            if result.returncode != 0:
                print("Failed to load Webcam modules:", result.stderr)
                return 1
            print(
                "Webcam has been enabled. If your webcam does not work yet, please reboot "
                + "to load any additional hardware-specific modules."
            )
            return 0
        case "off":
            with open(WEBCAM_MOD_FILE, "w", encoding="utf8") as fd:
                fd.write("\n".join([f"install {kmod} /bin/false" for kmod in WEBCAM_KMODS]) + "\n")
            os.chmod(WEBCAM_MOD_FILE, 0o644)
            print("Webcam has been disabled. Please reboot for the kernel modules to be unloaded.")
            return 0
        case _:
            print("Invalid inner script argument.")
            return 1


if __name__ == "__main__":
    sys.exit(main())
