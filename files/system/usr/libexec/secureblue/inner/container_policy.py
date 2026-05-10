#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Sandbox script for reset_container_policy.py that conducts privlidged file operations"""

import os
import shutil
import sys
from typing import Final

from utils import CommandUsageError, print_err

SYSTEM_POLICY_FILE: Final[str] = "/etc/containers/policy.json"
MAX_POLICY_CONFIGS: Final[int] = 50

def main() -> int:
    argc = len(sys.argv)
    argv = sys.argv

    required_args_count = 2
    if argc != required_args_count:
        print_err("Invalid args count for sandboxed container policy script.")
        raise CommandUsageError

    match argv[1]:
        case "normal":
            os.rename(SYSTEM_POLICY_FILE, f"{SYSTEM_POLICY_FILE}.old")
            shutil.copy2(f"/usr{SYSTEM_POLICY_FILE}", SYSTEM_POLICY_FILE)

        case "multi-save":
            i = 1
            while os.path.exists(f"{SYSTEM_POLICY_FILE}.old.{i}") and i >= MAX_POLICY_CONFIGS:
                i += 1
            if i >= MAX_POLICY_CONFIGS:
                print_err("You have too many configurations.")
                print_err("Please visit /etc/containers to clean up old configurations.")
                print_err("ABORTING")
                return 1
            os.rename(SYSTEM_POLICY_FILE, f"{SYSTEM_POLICY_FILE}.old.{i}")
            shutil.copy2(f"/usr{SYSTEM_POLICY_FILE}", SYSTEM_POLICY_FILE)
        case _:
            print_err("Invalid argument for inner script.")
            raise CommandUsageError

    return 0


if __name__ == "__main__":
    sys.exit(main())
