#!/usr/bin/env bash

set -oue pipefail

echo "Disabling NFS daemons"
systemctl disable nfs-idmapd
systemctl mask nfs-idmapd

systemctl disable nfs-mountd
systemctl mask nfs-mountd

systemctl disable nfsdcld
systemctl mask nfsdcld

systemctl disable rpc-gssd
systemctl mask rpc-gssd

systemctl disable rpc-statd-notify
systemctl mask rpc-statd-notify

systemctl disable rpc-statd
systemctl mask rpc-statd

systemctl disable rpcbind
systemctl mask rpcbind

systemctl disable gssproxy
systemctl mask gssproxy
