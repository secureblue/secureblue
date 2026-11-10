#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025 Universal Blue
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail
shopt -s nullglob

FEDORA_VERSION="$(rpm -E '%{fedora}')"

# Get latest stable Fedora kernel version and install corresponding secureblue kernel
KERNEL_VERSION="$(dnf repoquery \
    --repofrompath="updates-primary,https://dl.fedoraproject.org/pub/fedora/linux/updates/${FEDORA_VERSION}/Everything/${OS_ARCH}/" \
    --repo 'updates-primary' \
    --repo 'fedora' \
    --latest-limit 1 \
    --arch "${OS_ARCH}" \
    --queryformat '%{version}-%{release}.%{arch}' \
    'kernel'
)"

if [[ -z "${KERNEL_VERSION}" ]]; then
    echo "Failed to determine the upstream ${FEDORA_VERSION} kernel version for ${OS_ARCH}"
    exit 1
fi

secureblue_gpg_key_path="$(dnf repo info secureblue --json | jq -r '.[0].gpg_key.[0]')"
rpmkeys --import "${secureblue_gpg_key_path}"

SECUREBLUE_KERNEL_VERSION="${KERNEL_VERSION/.fc/.secureblue.*.fc}"
dnf --best --repo=secureblue -y download \
    "kernel-${SECUREBLUE_KERNEL_VERSION}" \
    "kernel-core-${SECUREBLUE_KERNEL_VERSION}" \
    "kernel-modules-${SECUREBLUE_KERNEL_VERSION}" \
    "kernel-modules-core-${SECUREBLUE_KERNEL_VERSION}"

if rpm -q kernel-modules-extra &>/dev/null; then
    dnf --best --repo=secureblue -y download "kernel-modules-extra-${SECUREBLUE_KERNEL_VERSION}"
fi

kernel_rpms_found=0
for kernel_rpm in kernel-[0-9]*."${OS_ARCH}".rpm; do
    (( ++kernel_rpms_found ))
done

if (( kernel_rpms_found == 1 )); then
    echo "Kernel RPM: ${kernel_rpm}"
else
    echo "Number of Kernel RPMs not one, found: ${kernel_rpms_found}"
    exit 1
fi

kernel_rpm_sans_prefix=${kernel_rpm#kernel-}
kernel_version=${kernel_rpm_sans_prefix%.fc*."${OS_ARCH}".rpm}
curl -fLsS --retry 5 -O "https://github.com/secureblue/kernel/releases/download/${kernel_version}/provenance.intoto.json"

VERIFIER_VERSION="v0.1.1"
if [[ "${OS_ARCH}" == x86_64 ]]; then
    VERIFIER_ARCH=amd64
    VERIFIER_SHA256=7053bb00052a64c77dbba4400636fd22d336c1b10aba9aac1db44744b9efba31
else
    VERIFIER_ARCH=arm64
    VERIFIER_SHA256=b46cbbdf75a0ea3a5595b1bb8fc9b3a8c5590f80017d4e7fb0d05fb471229b0d
fi

VERIFIER_PATH="slsa-verifier-${VERIFIER_VERSION}-linux-${VERIFIER_ARCH}"
curl -fLsS --retry 5 -O "https://github.com/slsa-framework/verifier/releases/download/${VERIFIER_VERSION}/${VERIFIER_PATH}"
echo "${VERIFIER_SHA256}  ${VERIFIER_PATH}" | sha256sum --check
chmod +x "${VERIFIER_PATH}"

"./${VERIFIER_PATH}" build provenance.intoto.json ./kernel-*.rpm \
    --level 3 \
    --require-signatures \
    --signer 'sigstore(identityMatch=regex)::https://token.actions.githubusercontent.com::https://github\.com/slsa-framework/actions/\.github/workflows/attest_actions\.yml@refs/tags/v[0-9]+\.[0-9]+\.[0-9]+' \
    --param 'expected_source:github.com/secureblue/kernel' \
    --param 'expected_branch:live' \
    --param 'trusted_builders:[https://github.com/secureblue/kernel/.github/workflows/kernel-build.yml@refs/heads/live]'

dnf --setopt=localpkg_gpgcheck=True --disable-repo=secureblue -y install ./kernel-*.rpm

kernel_rpm_sans_prefix_and_suffix=${kernel_rpm_sans_prefix%.rpm}
VMLINUZ_PATH="/usr/lib/modules/${kernel_rpm_sans_prefix_and_suffix}/vmlinuz"
sbverify --list "${VMLINUZ_PATH}"
