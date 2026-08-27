#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025 Universal Blue
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# Get latest stable Fedora kernel version and install corresponding secureblue kernel
KERNEL_VERSION="$(dnf repoquery \
    --repo 'updates' \
    --latest-limit 1 \
    --arch "${OS_ARCH}" \
    --queryformat '%{version}-%{release}.%{arch}' \
    'kernel'
)"
SECUREBLUE_KERNEL_VERSION="${KERNEL_VERSION/.fc/.secureblue.*.fc}"
dnf install --repo "copr:copr.fedorainfracloud.org:secureblue:packages" "kernel-${SECUREBLUE_KERNEL_VERSION}" -y

SECUREBLUE_NEW_KERNEL_VERSION="$(rpm -q 'kernel' --queryformat '%{VERSION}-%{RELEASE}.%{ARCH}')"
VMLINUZ_PATH="/usr/lib/modules/${SECUREBLUE_NEW_KERNEL_VERSION}/vmlinuz"
PUBLIC_KEY_DER_PATH='../system/usr/share/pki/akmods/certs/akmods-secureblue.der'
PUBLIC_KEY_CRT_PATH='./certs/public_key.crt'
PRIVATE_KEY_PATH='/tmp/certs/private_key.priv'

openssl x509 -in "${PUBLIC_KEY_DER_PATH}" -out "${PUBLIC_KEY_CRT_PATH}"
sbattach --remove "${VMLINUZ_PATH}"
sbsign --cert "${PUBLIC_KEY_CRT_PATH}" \
    --key "${PRIVATE_KEY_PATH}" \
    --output "${VMLINUZ_PATH}" \
    "${VMLINUZ_PATH}"
sbverify --list "${VMLINUZ_PATH}"
