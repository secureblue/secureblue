#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025 Universal Blue
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

mkdir -p /var/tmp
chmod 1777 /var/tmp

if [[ "$IMAGE_NAME" == *open* ]]; then
    nvidia_repo='fedora-nvidia'
else
    nvidia_repo='fedora-nvidia-580'
fi

dnf install -y --setopt=install_weak_deps=False "kernel-devel-matched-$(rpm -q 'kernel' --queryformat '%{VERSION}')"

dnf install -y --setopt=install_weak_deps=False akmods gcc-c++

# TODO remove this when fixed upstream
sed -i.backup -e '/if \[\[ -w \/var \]\] ; then/,/fi/d' /usr/sbin/akmodsbuild

dnf install -y --setopt=install_weak_deps=False \
    --enable-repo="${nvidia_repo}" \
    --disable-repo='fedora-multimedia' \
    nvidia-kmod-common nvidia-modprobe akmod-nvidia

KERNEL_VERSION="$(rpm -q "kernel" --queryformat '%{VERSION}-%{RELEASE}.%{ARCH}')"

echo "Installing kmod..."
akmods --force --kernels "${KERNEL_VERSION}" --kmod "nvidia"

mv /usr/sbin/akmodsbuild.backup /usr/sbin/akmodsbuild

modinfo /usr/lib/modules/"${KERNEL_VERSION}"/extra/nvidia/nvidia{,-drm,-modeset,-peermem,-uvm}.ko.xz > /dev/null || \
    { cat /var/cache/akmods/nvidia/*.failed.log && exit 1; }

# View license information
modinfo -l /usr/lib/modules/"${KERNEL_VERSION}"/extra/nvidia/nvidia{,-drm,-modeset,-peermem,-uvm}.ko.xz

./signmodules.sh "nvidia"

systemctl disable akmods-keygen@akmods-keygen.service
systemctl mask akmods-keygen@akmods-keygen.service
systemctl disable akmods-keygen.target
systemctl mask akmods-keygen.target
