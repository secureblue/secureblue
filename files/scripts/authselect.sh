#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -oue pipefail

echo "Enabling faillock in PAM authentication profile"

authselect enable-feature with-faillock 1> /dev/null