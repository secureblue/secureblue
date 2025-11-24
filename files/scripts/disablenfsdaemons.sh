#!/usr/bin/env bash

# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

set -oue pipefail

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
