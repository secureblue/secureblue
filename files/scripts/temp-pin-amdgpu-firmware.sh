#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# Temporarily pin amd-gpu-firmware until this issue is fixed:
# https://gitlab.freedesktop.org/drm/amd/-/work_items/5803
if rpm -q amd-gpu-firmware &>/dev/null; then
    dnf install -y --repo=updates-archive --setopt=install_weak_deps=False amd-gpu-firmware-20260810
    dnf versionlock add amd-gpu-firmware
fi
