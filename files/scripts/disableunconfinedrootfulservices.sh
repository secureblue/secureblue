#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -oue pipefail

systemctl disable uresourced.service
systemctl mask uresourced.service

systemctl mask --user uresourced.service

systemctl disable low-memory-monitor.service
systemctl mask low-memory-monitor.service

systemctl disable thermald.service
systemctl mask thermald.service
