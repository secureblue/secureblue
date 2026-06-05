#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Replace existing container policies with the default policy"""

import filecmp
import os
import shutil
import sys
from typing import Final

import sandbox
from utils import print_err

# Use absolute paths
SYSTEM_POLICY_FILE: Final[str] = "/etc/containers/policy.json"
USER_POLICY_FILE: Final[str] = os.path.expanduser("~/.config/containers/policy.json")

def main() -> int:
    """Main script entrypoint"""

    system_policy_default = None
    if os.path.exists(SYSTEM_POLICY_FILE):
        system_policy_default = filecmp.cmp(f"/usr{SYSTEM_POLICY_FILE}", SYSTEM_POLICY_FILE)
        if system_policy_default is False:
            # replace current policy with the system default
            container_function = sandbox.SandboxedFunction(
                "container_policy.py",
                read_write_paths=["/etc/containers", "/usr/etc/containers"],
            )
            sandbox.run(container_function)

    user_policy_default = None
    if os.path.exists(USER_POLICY_FILE):
        user_policy_default = filecmp.cmp(f"/usr{SYSTEM_POLICY_FILE}", USER_POLICY_FILE)
        if user_policy_default is False:
            # save current policy & replace user override with the default
            os.replace(USER_POLICY_FILE, f"{USER_POLICY_FILE}.old")
            shutil.copy2(f"/usr{SYSTEM_POLICY_FILE}", USER_POLICY_FILE)

    # notify the user that neither files exist and something is wrong
    if user_policy_default is None and system_policy_default is None:
        print_err("Warning: There is neither a system policy or a user policy! ! !")

    return 0


if __name__ == "__main__":
    sys.exit(main())
