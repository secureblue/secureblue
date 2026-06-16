#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
The sandboxed network filesystems toggle function
"""

import os
import subprocess
import sys
from typing import Final

NETFS_MODULES_FILE: Final[str] = "/etc/modprobe.d/99-network-filesystems.conf"

NETFS_MODULES: Final[list[str]] = [
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

NETFS_SERVICES: Final[list[str]] = [
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
    "gssproxy.service"
]


def main() -> int:
    """Set or remove the network filesystems module override"""
    required_args_count = 2
    if len(sys.argv) != required_args_count:
        return 1
    mode = sys.argv[1]
    match mode:
        case "on":
            with open(NETFS_MODULES_FILE, "w", encoding="utf8") as fd:
                for module in NETFS_MODULES:
                    fd.write(f"install {module} /sbin/modprobe --ignore-install {module}\n")
            os.chmod(NETFS_MODULES_FILE, 0o644)

            subprocess.run(["/usr/bin/systemctl", "unmask", "--", *NETFS_SERVICES], check=True)

            print("Network filesystems has been enabled. Reboot for effect.")
            return 0
        case "off":
            os.remove(NETFS_MODULES_FILE)

            subprocess.run(["/usr/bin/systemctl", "disable", "--now", "--", *NETFS_SERVICES], check=True)
            subprocess.run(["/usr/bin/systemctl", "mask", "--", *NETFS_SERVICES], check=True)

            print("Network filesystems has been disabled. Reboot for effect.")
            return 0
        case _:
            print("Invalid inner script argument.")
            return 1


if __name__ == "__main__":
    sys.exit(main())
