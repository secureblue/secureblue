#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

find /tmp/rpms

rpm-ostree cliwrap install-to-root /

QUALIFIED_KERNEL="$(rpm -qa | grep -P 'kernel-(\d+\.\d+\.\d+)' | sed -E 's/kernel-//')"
INCOMING_KERNEL_VERSION="$(basename -s .fc40.x86_64.rpm $(ls /tmp/rpms/kernel/kernel-[0-9]*.rpm 2>/dev/null | grep -P 'kernel-(\d+\.\d+\.\d+)' | sed -E 's/kernel-//'))"

echo "Qualified kernel: $QUALIFIED_KERNEL"
echo "Incoming kernel version: $INCOMING_KERNEL_VERSION"


if [[ "$FIRST_KERNEL_VERSION" != "$QUALIFIED_KERNEL" ]]; then
    echo "Installing kernel from kernel-cache."
    rpm-ostree override replace \
        --experimental \
        --install=zstd \
        /tmp/rpms/kernel/kernel-[0-9]*.rpm \
        /tmp/rpms/kernel/kernel-core-*.rpm \
        /tmp/rpms/kernel/kernel-modules-*.rpm
else
    echo "Skipping installation: version matches installed kernel ($QUALIFIED_KERNEL)"
fi