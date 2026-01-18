#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -oue pipefail



if [[ "$IMAGE_NAME" != *"securecore"* ]]; then
  KERNEL_VERSION="6.17.12-300"
  KERNEL_HEADERS_VERSION="6.17.4-300"
  
  dnf install -y --from-repo=updates-archive \
    "kernel-${KERNEL_VERSION}.fc${OS_VERSION}" \
    "kernel-core-${KERNEL_VERSION}.fc${OS_VERSION}" \
    "kernel-modules-${KERNEL_VERSION}.fc${OS_VERSION}" \
    "kernel-modules-core-${KERNEL_VERSION}.fc${OS_VERSION}" \
    "kernel-modules-extra-${KERNEL_VERSION}.fc${OS_VERSION}" \
    "kernel-tools-${KERNEL_VERSION}.fc${OS_VERSION}" \
    "kernel-tools-libs-${KERNEL_VERSION}.fc${OS_VERSION}" \
    "kernel-headers-${KERNEL_HEADERS_VERSION}.fc${OS_VERSION}"
fi