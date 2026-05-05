#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

echo "Disabling the sssd daemons"
systemctl disable sssd.service
systemctl mask sssd.service

systemctl disable sssd-kcm.service
systemctl mask sssd-kcm.service

systemctl disable sssd-kcm.socket
systemctl mask sssd-kcm.socket