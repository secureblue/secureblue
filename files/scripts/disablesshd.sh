#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

echo "Disabling sshd"

systemctl disable sshd.service
systemctl mask sshd.service

systemctl disable sshd.socket
systemctl mask sshd.socket

systemctl disable sshd-unix-local.socket 2>/dev/null || true
systemctl mask sshd-unix-local.socket 2>/dev/null || true

systemctl disable sshd-keygen.target 2>/dev/null || true
systemctl mask sshd-keygen.target 2>/dev/null || true