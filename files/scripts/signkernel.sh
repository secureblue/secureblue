#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025 Universal Blue
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

KERNEL_VERSION="$(rpm -q "kernel" --queryformat '%{VERSION}-%{RELEASE}.%{ARCH}')"

PUBLIC_KEY_DER_PATH="../system/etc/pki/akmods/certs/akmods-secureblue.der"
PUBLIC_KEY_CRT_PATH="./certs/public_key.crt"
PRIVATE_KEY_PATH="/tmp/certs/private_key.priv"

openssl x509 -in "$PUBLIC_KEY_DER_PATH" -out "$PUBLIC_KEY_CRT_PATH"
sbsign --cert "$PUBLIC_KEY_CRT_PATH" --key "$PRIVATE_KEY_PATH" /usr/lib/modules/"${KERNEL_VERSION}"/vmlinuz --output /usr/lib/modules/"${KERNEL_VERSION}"/vmlinuz
sbverify --list /usr/lib/modules/"${KERNEL_VERSION}"/vmlinuz
