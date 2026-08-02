#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Replace existing container policy overrides with the default system container policy"""

import filecmp
import os
import shutil
import sys
from typing import Final

import sandbox
from utils import print_err

# Use absolute paths
SYSTEM_POLICY_FILE: Final[str] = "/etc/containers/policy.json"
DEFAULT_SYSTEM_POLICY_FILE: Final[str] = f"/usr{SYSTEM_POLICY_FILE}"
USER_POLICY_FILE: Final[str] = os.path.expanduser("~/.config/containers/policy.json")

def main() -> int:
    """Main script entrypoint"""

    system_policy_default = None
    if os.path.exists(SYSTEM_POLICY_FILE):
        system_policy_default = filecmp.cmp(DEFAULT_SYSTEM_POLICY_FILE, SYSTEM_POLICY_FILE)
        if system_policy_default is False:
            # replace system override with the system default
            container_function = sandbox.SandboxedFunction(
                "container_policy.py",
                read_write_paths=["/etc/containers", "/usr/etc/containers"],
            )
            sandbox.run(container_function)
            print(f"Replaced override file at {SYSTEM_POLICY_FILE} with the system default container policy.")

    user_policy_default = None
    if os.path.exists(USER_POLICY_FILE):
        user_policy_default = filecmp.cmp(DEFAULT_SYSTEM_POLICY_FILE, USER_POLICY_FILE)
        if user_policy_default is False:
            # replace user override with the system default
            shutil.copy2(DEFAULT_SYSTEM_POLICY_FILE, USER_POLICY_FILE)
            print(f"Replaced container policy override at {USER_POLICY_FILE} with the system default policy.")

    # notify the user when neither files exist (something is wrong)
    if user_policy_default is None and system_policy_default is None:
        print_err("No system or user container policy override was found!")

    return 0


if __name__ == "__main__":
    sys.exit(main())