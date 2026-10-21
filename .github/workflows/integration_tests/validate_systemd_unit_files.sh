#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euxo pipefail

# Check systemd unit files for correctness.
systemd-analyze verify --recursive-errors=yes multi-user.target
systemd-analyze verify --user --recursive-errors=yes default.target
