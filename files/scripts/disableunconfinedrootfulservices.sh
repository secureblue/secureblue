#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

systemctl disable uresourced.service
systemctl mask uresourced.service

systemctl mask --user uresourced.service

systemctl disable low-memory-monitor.service 2>/dev/null || true
systemctl mask low-memory-monitor.service 2>/dev/null || true

systemctl disable thermald.service 2>/dev/null || true
systemctl mask thermald.service 2>/dev/null || true
