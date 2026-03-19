#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

rpm_ostree_version=$(rpm -q --qf '%{version}-%{release}' rpm-ostree)
bad_version="2026.1-1.fc${OS_VERSION}"
if [ "${rpm_ostree_version}" = "${bad_version}" ]; then
    echo "Broken rpm-ostree version (${rpm_ostree_version}) detected; making build fail."
    exit 1
fi
