#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

if [[ "${OS_ARCH}" == 'x86_64' ]]; then
    dnf install -y --setopt=install_weak_deps=False dangerzone
else
    echo 'Dangerzone is only available on x86-64 architecture; skipping installation.'
fi
