#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Update system (with provenance verification)."""

import sys
from pathlib import Path
from subprocess import DEVNULL, CalledProcessError, Popen, run


def main() -> int:
    try:
        run(["/usr/libexec/secureblue/verify-provenance.sh"], check=True)
        run(["/usr/bin/rpm-ostree", "upgrade"], check=True)
        if Path("/usr/libexec/secureblue/security-update-notification").is_file():
            Popen(
                ["/usr/libexec/secureblue/security-update-notification"],
                start_new_session=True,
                stdout=DEVNULL,
                stderr=DEVNULL,
            )
        return 0
    except CalledProcessError:
        print("An unexpected error occured.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
