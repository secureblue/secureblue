#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

find /tmp/rpms

rpm-ostree cliwrap install-to-root /

QUALIFIED_KERNEL="$(rpm -qa | grep -P 'kernel-(\d+\.\d+\.\d+)' | sed -E 's/kernel-//')"
INCOMING_KERNEL_VERSION="$(basename -s .rpm $(ls /tmp/rpms/kernel/kernel-[0-9]*.rpm 2>/dev/null | grep -P 'kernel-(\d+\.\d+\.\d+)' | sed -E 's/kernel-//'))"

echo "Qualified kernel: $QUALIFIED_KERNEL"
echo "Incoming kernel version: $INCOMING_KERNEL_VERSION"


if [[ "$INCOMING_KERNEL_VERSION" != "$QUALIFIED_KERNEL" ]]; then
    echo "Installing kernel rpm from kernel-cache."
    rpm-ostree override replace \
        --experimental \
        --install=zstd \
        /tmp/rpms/kernel/kernel-[0-9]*.rpm \
        /tmp/rpms/kernel/kernel-core-*.rpm \
        /tmp/rpms/kernel/kernel-modules-*.rpm
else
    echo "Installing kernel files from kernel-cache."
    cd /tmp
    rpm2cpio /tmp/rpms/kernel/kernel-core-*.rpm | cpio -idmv
    cp ./lib/modules/*/vmlinuz /usr/lib/modules/*/vmlinuz
    cd /
fi