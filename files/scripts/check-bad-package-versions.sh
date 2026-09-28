#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

bad_packages=(
    'rpm-ostree-2026.1-1.fc*'
)

for pkg in "${bad_packages[@]}"; do
    if installed_pkg=$(rpm -q --qf '%{version}-%{release}' "${pkg}"); then
        echo "Broken package version ${installed_pkg} detected; making build fail."
        exit 1
    fi
done
