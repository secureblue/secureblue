#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

QUALIFIED_KERNEL="$(rpm -qa | grep -P 'kernel-(\d+\.\d+\.\d+)' | sed -E 's/kernel-//')"
/usr/bin/dracut --no-hostonly --kver "$QUALIFIED_KERNEL" --reproducible -v --add ostree -f "/lib/modules/$QUALIFIED_KERNEL/initramfs.img"
chmod 0600 "/lib/modules/$QUALIFIED_KERNEL/initramfs.img"