#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -oue pipefail

echo "Disabling print services"

systemctl disable cups.socket
systemctl mask cups.socket

systemctl disable cups.service
systemctl mask cups.service

systemctl disable cups-browsed.service
systemctl mask cups-browsed.service
