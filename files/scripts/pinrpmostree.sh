#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -oue pipefail

RPM_OSTREE_VERSION="2025.12-1"

dnf install -y --from-repo=updates-archive \
  "rpm-ostree-${RPM_OSTREE_VERSION}.fc${OS_VERSION}" \
  "rpm-ostree-libs-${RPM_OSTREE_VERSION}.fc${OS_VERSION}"