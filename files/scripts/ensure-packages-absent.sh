#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

packages=(blender sudo sushi plocate)

for pkg in "${packages[@]}"; do
    if rpm -q "${pkg}" &> /dev/null; then
        echo "${pkg} found. Exiting..."
        exit 1
    fi
done
