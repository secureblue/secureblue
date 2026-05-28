#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

echo "Disabling iSCSI daemons"

systemctl disable iscsid.service 2>/dev/null || true
systemctl mask iscsid.service 2>/dev/null || true

systemctl disable iscsid.socket 2>/dev/null || true
systemctl mask iscsid.socket 2>/dev/null || true

systemctl disable iscsiuio.service 2>/dev/null || true
systemctl mask iscsiuio.service 2>/dev/null || true

systemctl disable iscsiuio.socket 2>/dev/null || true
systemctl mask iscsiuio.socket 2>/dev/null || true
