#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# Enable all system or user services that are preset to be enabled.
systemctl preset-all --preset-mode=enable-only
systemctl --global preset-all --preset-mode=enable-only
