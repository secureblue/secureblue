#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

echo "Disabling systemd sshd vsock socket"

# For more info, see https://blog.nsrun.io/2026/01/15/systemd-vsock-openssh-server/
systemctl disable sshd-vsock.socket
systemctl mask sshd-vsock.socket
