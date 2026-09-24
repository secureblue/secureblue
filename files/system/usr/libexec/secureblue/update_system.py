#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Update system (with provenance verification)."""

import sys
from pathlib import Path
from subprocess import DEVNULL, CalledProcessError, Popen, run

from utils import BootcBackend


def main() -> int:
    try:
        run(["/usr/libexec/secureblue/verify-provenance.sh"], check=True)

        if BootcBackend.from_running() == BootcBackend.OSTREE:
            run(["/usr/bin/rpm-ostree", "upgrade"], check=True)
            if Path("/usr/libexec/secureblue/security-update-notification").is_file():
                Popen(
                    ["/usr/libexec/secureblue/security-update-notification"],
                    start_new_session=True,
                    stdout=DEVNULL,
                    stderr=DEVNULL,
                )
        else:
            print("You must be authorized as an administrator to trigger an update.")
            run(["/usr/bin/run0", "--via-shell", "/usr/bin/bootc", "upgrade"], check=True)
        return 0
    except CalledProcessError:
        print("An unexpected error occurred.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
