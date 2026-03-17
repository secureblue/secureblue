#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

echo 'install_items+=" /usr/lib64/libno_rlimit_as.so "' > /etc/dracut.conf.d/libno_rlimit_as.conf