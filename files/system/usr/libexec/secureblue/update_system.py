#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Update system (with provenance verification)."""

import sys
from pathlib import Path
from subprocess import CalledProcessError, run


def main() -> int:
    try:
        run(["/usr/libexec/secureblue/verify-provenance.sh"], check=True)
        run(["/usr/bin/rpm-ostree", "upgrade"], check=True)
        if Path("/usr/libexec/secureblue/security-update-notification").is_file:
            run(
                ["/usr/libexec/secureblue/security-update-notification"],
                check=True,
                capture_output=True,
            )
        return 0
    except CalledProcessError:
        print("An unexpected error occured.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
