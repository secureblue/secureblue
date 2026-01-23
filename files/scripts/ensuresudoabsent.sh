#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

if command -v sudo &> /dev/null
then
    echo "sudo found. Exiting..."
    exit 1
fi