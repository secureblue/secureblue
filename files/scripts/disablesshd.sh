#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -oue pipefail

echo "Disabling sshd"

systemctl disable sshd.service
systemctl mask sshd.service

systemctl disable sshd.socket
systemctl mask sshd.socket

systemctl disable sshd-unix-local.socket
systemctl mask sshd-unix-local.socket

systemctl disable sshd-keygen.target
systemctl mask sshd-keygen.target