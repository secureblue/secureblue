#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import os
import subprocess
import sys
from typing import Final

MODULES_FILE: Final[str] = "/etc/modprobe.d/99-network-filesystems.conf"

MODULES: Final[list[str]] = [
    "nfsv4",
    "nfs_acl",
    "nfs_localio",
    "nfsd",
    "nfs_layout_flexfiles",
    "nfs_layout_nfsv41_files",
    "grace",
    "lockd",
    "auth_rpcgss",
    "rpcsec_gss_krb5",
    "sunrpc",
    "cifs",
    "ksmbd",
]

UNITS: Final[list[str]] = [
    "nfs-idmapd.service",
    "nfs-client.target",
    "nfs-blkmap.service",
    "nfs-mountd.service",
    "nfsdcld.service",
    "nfs-server.service",
    "nfs-utils.service",
    "rpc-gssd.service",
    "rpc-statd-notify.service",
    "rpc-statd.service",
    "rpcbind.service",
    "rpcbind.socket",
    "rpcbind.target",
    "rpc_pipefs.target",
    "var-lib-nfs-rpc_pipefs.mount",
    "gssproxy.service",
]

NOTE: Final[str] = """\
Network filesystems unmasked.
Enable the services as needed.

Note: Secureblue strongly recommends against enabling all network filesystems services at once.
Only enable the services you need for your use case."""


def enable_units() -> None:
    with open(MODULES_FILE, "w", encoding="utf8") as fd:
        fd.writelines(
            f"install {module} /sbin/modprobe --ignore-install {module}\n" for module in MODULES
        )
    os.chmod(MODULES_FILE, 0o644)

    subprocess.run(["/usr/bin/systemctl", "unmask", "--quiet", *UNITS], check=True)
    subprocess.run(["/usr/bin/systemctl", "daemon-reload"], check=True)


def disable_units() -> None:
    os.remove(MODULES_FILE)

    subprocess.run(["/usr/bin/systemctl", "disable", "--now", "--quiet", *UNITS], check=True)
    subprocess.run(["/usr/bin/systemctl", "mask", "--now", "--quiet", *UNITS], check=True)
    subprocess.run(["/usr/bin/systemctl", "daemon-reload"], check=True)


def main() -> int:
    required_args_count = 2
    if len(sys.argv) != required_args_count:
        return 1

    mode = sys.argv[1].casefold()
    try:
        match mode:
            case "on":
                enable_units()
                print(NOTE)
                return 0
            case "off":
                disable_units()
                print("Network filesystems disabled.")
                return 0
            case _:
                print("Please provide a valid argument (on/off).")
                return 1
    except subprocess.CalledProcessError:
        print("An unexpected error occured.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
