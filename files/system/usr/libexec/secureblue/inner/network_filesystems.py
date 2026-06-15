#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
The sandboxed network filesystems toggle function
"""

import os
import sys
from typing import Final

from utils import SystemdService

NETFS_MOD_FILE: Final[str] = "/etc/modprobe.d/99-network-filesystems.conf"
NETFS_MOD_TEXT: Final[str] = """install nfs /sbin/modprobe --ignore-install nfs
install nfsv4 /sbin/modprobe --ignore-install nfsv4
install nfs_acl /sbin/modprobe --ignore-install nfs_acl
install nfs_localio /sbin/modprobe --ignore-install nfs_localio
install nfsd /sbin/modprobe --ignore-install nfsd
install nfs_layout_flexfiles /sbin/modprobe --ignore-install nfs_layout_flexfiles
install nfs_layout_nfsv41_files /sbin/modprobe --ignore-install nfs_layout_nfsv41_files
install grace /sbin/modprobe --ignore-install grace
install lockd /sbin/modprobe --ignore-install lockd
install auth_rpcgss /sbin/modprobe --ignore-install auth_rpcgss
install rpcsec_gss_krb5 /sbin/modprobe --ignore-install rpcsec_gss_krb5
install sunrpc /sbin/modprobe --ignore-install sunrpc
install cifs /sbin/modprobe --ignore-install cifs
install ksmbd /sbin/modprobe --ignore-install ksmbd
"""


def main() -> int:
    """Set or remove the network filesystems module override"""
    required_args_count = 2
    if len(sys.argv) != required_args_count:
        return 1
    netfs_services = [
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
    mode = sys.argv[1]
    match mode:
        case "on":
            with open(NETFS_MOD_FILE, "w", encoding="utf8") as fd:
                fd.write(NETFS_MOD_TEXT)
            os.chmod(NETFS_MOD_FILE, 0o644)

            for netfs_service in netfs_services:
                SystemdService(netfs_service).unmask()

            print("Network filesystems has been enabled. Reboot for effect.")
            return 0
        case "off":
            os.remove(NETFS_MOD_FILE)

            for netfs_service in netfs_services:
                SystemdService(netfs_service).mask()

            print("Network filesystems has been disabled. Reboot for effect.")
            return 0
        case _:
            print("Invalid inner script argument.")
            return 1


if __name__ == "__main__":
    sys.exit(main())
