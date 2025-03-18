#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

find /tmp/rpms

QUALIFIED_KERNEL="$(rpm -qa | grep -P 'kernel-(\d+\.\d+\.\d+)' | sed -E 's/kernel-//')"
INCOMING_KERNEL_VERSION="$(find '/tmp/rpms/kernel' \
    -maxdepth 1 \
    -name 'kernel-[0-9]*.rpm' \
    -regextype posix-egrep \
    -regex '.*/kernel-([0-9]+\.[0-9]+\.[0-9]+).*' \
    -printf '%f' \
    -quit | sed -e 's/^kernel-//' -e 's/.rpm$//')"

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
