#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

echo "Masking systemd-nsresourced"

systemctl mask systemd-nsresourced.service 2>/dev/null || true
systemctl mask systemd-nsresourced.socket 2>/dev/null || true
