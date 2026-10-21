#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

umask 022
rm -f /run/extensions/secureblue-dev.raw
systemd-sysext refresh
