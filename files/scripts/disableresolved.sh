#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -oue pipefail

echo "Disabling systemd-resolved DNS resolver"

systemctl disable systemd-resolved.service
systemctl mask systemd-resolved.service
