#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

echo "Disabling NFS daemons"

systemctl disable nfs-idmapd.service 2>/dev/null || true
systemctl mask nfs-idmapd.service 2>/dev/null || true

systemctl disable nfs-client.target 2>/dev/null || true
systemctl mask nfs-client.target 2>/dev/null || true

systemctl disable nfs-blkmap.service 2>/dev/null || true
systemctl mask nfs-blkmap.service 2>/dev/null || true

systemctl disable nfs-mountd.service 2>/dev/null || true
systemctl mask nfs-mountd.service 2>/dev/null || true

systemctl disable nfsdcld.service 2>/dev/null || true
systemctl mask nfsdcld.service 2>/dev/null || true

systemctl disable nfs-server.service 2>/dev/null || true
systemctl mask nfs-server.service 2>/dev/null || true

systemctl disable nfs-utils.service 2>/dev/null || true
systemctl mask nfs-utils.service 2>/dev/null || true

systemctl disable rpc-gssd.service 2>/dev/null || true
systemctl mask rpc-gssd.service 2>/dev/null || true

systemctl disable rpc-statd-notify.service 2>/dev/null || true
systemctl mask rpc-statd-notify.service 2>/dev/null || true

systemctl disable rpc-statd.service 2>/dev/null || true
systemctl mask rpc-statd.service 2>/dev/null || true

systemctl disable rpcbind.service 2>/dev/null || true
systemctl mask rpcbind.service 2>/dev/null || true

systemctl disable rpcbind.socket 2>/dev/null || true
systemctl mask rpcbind.socket 2>/dev/null || true

systemctl disable rpcbind.target 2>/dev/null || true
systemctl mask rpcbind.target 2>/dev/null || true

systemctl disable rpc_pipefs.target 2>/dev/null || true
systemctl mask rpc_pipefs.target 2>/dev/null || true

systemctl mask var-lib-nfs-rpc_pipefs.mount 2>/dev/null || true

systemctl disable gssproxy.service 2>/dev/null || true
systemctl mask gssproxy.service 2>/dev/null || true
