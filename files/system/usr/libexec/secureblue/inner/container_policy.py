#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Sandbox script for reset_container_policy.py that conducts privileged file operations"""

import os
import shutil
import sys


def main() -> int:
    system_policy_file = "/etc/containers/policy.json"
    os.replace(system_policy_file, f"{system_policy_file}.old")
    shutil.copy2(f"/usr{system_policy_file}", system_policy_file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
