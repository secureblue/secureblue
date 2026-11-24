#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025 Universal Blue
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

mkdir -p /var/tmp
chmod 1777 /var/tmp

if [[ "${IMAGE_NAME}" == *open* ]]; then
    nvidia_repo='fedora-nvidia'
else
    nvidia_repo='fedora-nvidia-580'
fi

KERNEL_VERSION="$(rpm -q 'kernel' --queryformat '%{VERSION}-%{RELEASE}.%{ARCH}')"

dnf --best --repo=secureblue -y download \
    "kernel-devel-${KERNEL_VERSION}" \
    "kernel-devel-matched-${KERNEL_VERSION}"

provenance_file='provenance.intoto.json'
curl -fLsS --retry 5 -O "https://github.com/secureblue/kernel/releases/download/${KERNEL_VERSION%.fc*}/${provenance_file}"

slsa-verifier build "${provenance_file}" ./kernel-devel-*.rpm \
    --level 3 \
    --require-signatures \
    --signer 'sigstore(identityMatch=regex)::https://token.actions.githubusercontent.com::https://github\.com/slsa-framework/actions/\.github/workflows/attest_actions\.yml@refs/tags/v[0-9]+\.[0-9]+\.[0-9]+' \
    --param 'expected_source:github.com/secureblue/kernel' \
    --param 'expected_branch:live' \
    --param 'trusted_builders:[https://github.com/secureblue/kernel/.github/workflows/kernel-build.yml@refs/heads/live]'

rm "${provenance_file}"

dnf --setopt=localpkg_gpgcheck=True --setopt=install_weak_deps=False --disable-repo=secureblue -y install ./kernel-devel-*.rpm

rm ./kernel-devel-*.rpm

dnf install -y --setopt=install_weak_deps=False akmods gcc-c++

# TODO remove this when fixed upstream
sed -i.backup -e '/if \[\[ -w \/var \]\] ; then/,/fi/d' /usr/sbin/akmodsbuild

dnf install -y --setopt=install_weak_deps=False \
    --enable-repo="${nvidia_repo}" \
    --disable-repo='fedora-multimedia' \
    nvidia-kmod-common nvidia-modprobe akmod-nvidia

echo "Installing kmod..."
akmods --force --kernels "${KERNEL_VERSION}" --kmod "nvidia"

mv /usr/sbin/akmodsbuild.backup /usr/sbin/akmodsbuild

modinfo /usr/lib/modules/"${KERNEL_VERSION}"/extra/nvidia/nvidia{,-drm,-modeset,-peermem,-uvm}.ko.xz > /dev/null || \
    { cat /var/cache/akmods/nvidia/*.failed.log && exit 1; }

# View license information
modinfo -l /usr/lib/modules/"${KERNEL_VERSION}"/extra/nvidia/nvidia{,-drm,-modeset,-peermem,-uvm}.ko.xz

systemctl disable akmods-keygen@akmods-keygen.service
systemctl mask akmods-keygen@akmods-keygen.service
systemctl disable akmods-keygen.target
systemctl mask akmods-keygen.target
