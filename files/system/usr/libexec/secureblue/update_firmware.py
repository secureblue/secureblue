#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Update device firmware."""

import sys
from subprocess import CalledProcessError, run


def main() -> int:
    try:
        run(["/usr/bin/fwupdmgr", "refresh", "--force"], check=True)
        run(["/usr/bin/fwupdmgr", "get-updates"], check=False)
        run(["/usr/bin/fwupdmgr", "update"], check=True)
        return 0
    except CalledProcessError:
        print("An unexpected error occured.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
