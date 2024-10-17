#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

find /tmp/rpms

rpm-ostree cliwrap install-to-root /

echo "Install kernel from kernel-cache."
rpm-ostree override replace \
    --experimental \
    --install=zstd \
    /tmp/rpms/kernel/kernel-[0-9]*.rpm \
    /tmp/rpms/kernel/kernel-core-*.rpm \
    /tmp/rpms/kernel/kernel-modules-*.rpm