#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

echo "Disabling avahi-daemon"

systemctl disable avahi-daemon.socket
systemctl mask avahi-daemon.socket

systemctl disable avahi-daemon.service
systemctl mask avahi-daemon.service
