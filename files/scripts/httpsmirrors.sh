#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail
shopt -s nullglob

sed -i -e 's/metalink?/metalink?protocol=https\&/g' \
    /usr/share/dnf5/repos.d/*.repo \
    /etc/yum.repos.d/*.repo
