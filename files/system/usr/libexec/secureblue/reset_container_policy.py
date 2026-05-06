#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Replace existing container policies with the default policy"""

import filecmp
import os
import sys
from typing import Final

import sandbox
from utils import print_err

# Use absolute paths
SYSTEM_POLICY_FILE: Final[str] = "/etc/containers/policy.json"
USER_POLICY_FILE: Final[str] = os.path.expanduser("~/.config/containers/policy.json")
MAX_POLICY_CONFIGS: Final[int] = 50

def main() -> int:
    """Main script entrypoint"""

    conatiner_function = sandbox.SandboxedFunction(
        "container_policy.py",
        read_write_paths=["/etc/containers", "/usr/etc/containers"],
        capabilities=["CAP_DAC_OVERRIDE"]
    )

    # replace system policy file
    if not filecmp.cmp(f"/usr{SYSTEM_POLICY_FILE}", SYSTEM_POLICY_FILE):
        if not os.path.exists(f"{SYSTEM_POLICY_FILE}.old"):
            # all requirements met
            sandbox.run(conatiner_function, "normal")
        else:
            # An old config is already present
            sandbox.run(conatiner_function, "multi-save")

    # replace user override
    if os.path.exists(USER_POLICY_FILE):
        if os.path.exists(f"{USER_POLICY_FILE}.old"):
            i = 1
            while os.path.exists(f"{USER_POLICY_FILE}.old.{i}") and i >= MAX_POLICY_CONFIGS:
                i += 1
            if i >= MAX_POLICY_CONFIGS:
                print_err("You have too many configurations.")
                print_err("Please visit ~/.config/containers to clean up old configurations.")
                print_err("ABORTING")
                return 1
            os.rename(USER_POLICY_FILE, f"{USER_POLICY_FILE}.old.{i}")
        else:
            os.rename(USER_POLICY_FILE, f"{USER_POLICY_FILE}.old")

    return 0


if __name__ == "__main__":
    sys.exit(main())
