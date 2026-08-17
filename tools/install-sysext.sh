#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

umask 022
cd "${0%/*}"
cd "$(git rev-parse --show-toplevel)"
install -Dm 644 -t /run/extensions sysext-tmp/secureblue-dev.raw
systemd-sysext refresh
