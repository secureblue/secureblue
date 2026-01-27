#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

echo "Disabling NFS daemons"

systemctl disable nfs-idmapd.service
systemctl mask nfs-idmapd.service

systemctl disable nfs-client.target
systemctl mask nfs-client.target

systemctl disable nfs-blkmap.service
systemctl mask nfs-blkmap.service

systemctl disable nfs-mountd.service
systemctl mask nfs-mountd.service

systemctl disable nfsdcld.service
systemctl mask nfsdcld.service

systemctl disable nfs-server.service
systemctl mask nfs-server.service

systemctl disable nfs-utils.service
systemctl mask nfs-utils.service

systemctl disable rpc-gssd.service
systemctl mask rpc-gssd.service

systemctl disable rpc-statd-notify.service
systemctl mask rpc-statd-notify.service

systemctl disable rpc-statd.service
systemctl mask rpc-statd.service

systemctl disable rpcbind.service
systemctl mask rpcbind.service

systemctl disable rpcbind.socket
systemctl mask rpcbind.socket

systemctl disable rpcbind.target
systemctl mask rpcbind.target

systemctl disable rpc_pipefs.target

systemctl disable gssproxy.service
systemctl mask gssproxy.service
