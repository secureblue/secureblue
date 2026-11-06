#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# Nvidia repos only used during build process
rm -f \
    /usr/share/dnf5/repos.d/negativo17-fedora-nvidia.repo \
    /usr/share/dnf5/repos.d/fedora-nvidia-580.repo \
    /usr/share/dnf5/repos.d/nvidia-container-toolkit.repo
