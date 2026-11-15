#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euxo pipefail

if ! systemctl --user is-active oo7-daemon.service; then
    systemctl --user status oo7-daemon.service
    exit 1
fi
