#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# rar is only provided for x86_64
if [[ "$OS_ARCH" == 'x86_64' ]]; then
    dnf install --setopt=install_weak_deps=False -y rar
else
    dnf install --setopt=install_weak_deps=False -y unrar
fi