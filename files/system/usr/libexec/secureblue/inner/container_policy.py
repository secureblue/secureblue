#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
The sandboxed function to reset the system container policy
"""

import shutil
import sys


def main() -> int:
    system_policy_file = "/etc/containers/policy.json"
    shutil.copy2(f"/usr{system_policy_file}", system_policy_file)
    return 0


if __name__ == "__main__":
    sys.exit(main())