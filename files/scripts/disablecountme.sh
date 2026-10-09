#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

echo "Disabling rpm-ostree-countme"

systemctl disable rpm-ostree-countme.timer 2>/dev/null || true
systemctl mask rpm-ostree-countme.timer 2>/dev/null || true

systemctl disable rpm-ostree-countme.service 2>/dev/null || true
systemctl mask rpm-ostree-countme.service 2>/dev/null || true
