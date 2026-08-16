#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Update system (with provenance verification)."""

import os
import sys
from pathlib import Path
from subprocess import DEVNULL, CalledProcessError, Popen, run


def run_bootc_or_rpm_ostree_upgrade() -> None:
    """Upgrade using bootc if possible, or rpm-ostree if not."""
    is_root = os.geteuid() == 0
    if is_root:
        check_cmd = ["/usr/bin/bootc", "upgrade", "--check"]
    else:
        check_cmd = ["/usr/libexec/secureblue/secureblue-priv-cmd", "bootc-upgrade-check"]
    check_result = run(check_cmd, check=False, capture_output=True, text=True)
    use_rpm_ostree = "local rpm-ostree modifications" in check_result.stderr

    if use_rpm_ostree:
        upgrade_cmd = ["/usr/bin/rpm-ostree", "upgrade"]
    elif is_root:
        upgrade_cmd = ["/usr/bin/bootc", "upgrade"]
    else:
        upgrade_cmd = ["/usr/libexec/secureblue/secureblue-priv-cmd", "bootc-upgrade"]
    run(upgrade_cmd, check=True)


def main() -> int:
    try:
        run(["/usr/libexec/secureblue/verify-provenance.sh"], check=True)
        run_bootc_or_rpm_ostree_upgrade()
        if Path("/usr/libexec/secureblue/security-update-notification").is_file():
            Popen(
                ["/usr/libexec/secureblue/security-update-notification"],
                start_new_session=True,
                stdout=DEVNULL,
                stderr=DEVNULL,
            )
        return 0
    except CalledProcessError:
        print("An unexpected error occurred.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
