#!/usr/bin/python3 -I

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import sys
from subprocess import CalledProcessError, run
from time import sleep

RPM_OSTREE_UNITS: list[str] = [
    "rpm-ostreed-automatic.service",
    "rpm-ostreed-automatic.timer",
]

FILES_TO_REMOVE: list[str] = [
    "/etc/containers/policy.json",
    "/etc/containers/registries.d/secureblue.yaml",
    "/etc/pki/containers/secureblue-2025.pub",
    "/etc/systemd/system/rpm-ostreed.service.d/coreos-containers-policy.conf",
    "/opt/install_secureblue.py",
    "/root/akmods-secureblue.der",
]


def main() -> int:
    try:
        run(["/usr/bin/sudo", "/usr/bin/systemctl", "stop", *RPM_OSTREE_UNITS], check=True)

        run(["/usr/bin/sudo", "/usr/bin/mokutil", "--timeout", "-1"], check=True)
        print('The next line will prompt for a MOK password. Input "secureblue".')
        run(
            ["/usr/bin/sudo", "/usr/bin/mokutil", "--import", "/root/akmods-secureblue.der"],
            check=True,
        )

        print(
            "At next reboot, the mokutil UEFI menu UI will be displayed "
            "(QWERTY keyboard input and navigation)."
        )
        print('Then, select "Enroll MOK", and input "secureblue" as the password.')

        print("Rebasing to securecore (secureblue CoreOS image)...")
        run(
            [
                "/usr/bin/sudo",
                "/usr/bin/rpm-ostree",
                "rebase",
                f"ostree-image-signed:docker://ghcr.io/secureblue/securecore-{sys.argv[1]}",
            ],
            check=True,
        )

        with open("/var/home/core/.bash_profile") as profile:
            lines: list[str] = profile.readlines()
        with open("/var/home/core/.bash_profile", "w") as profile:
            profile.writelines(line for line in lines if "/opt/install_securecore.py" not in line)

        run(["/usr/bin/sudo", "/usr/bin/rm", "-f", *FILES_TO_REMOVE], check=True)

        print("Automatically rebooting in 5 seconds...")
        sleep(5)
        run(["/usr/bin/sudo", "/usr/bin/systemctl", "reboot"], check=True)

    except (CalledProcessError, OSError) as error:
        print(error, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
