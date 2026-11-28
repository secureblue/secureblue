#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

rm -f /usr/lib/systemd/system/rpm-ostreed.service.d/coreos-containers-policy.conf
rm -f /usr/lib/coreos/coreos-containers-policy.json
