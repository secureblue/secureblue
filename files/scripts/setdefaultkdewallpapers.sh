#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -oue pipefail

ln -sf /usr/share/backgrounds/secureblue/secureblue-blue.png /usr/share/backgrounds/default.png
ln -sf /usr/share/backgrounds/secureblue/secureblue-black.png /usr/share/backgrounds/default-dark.png

ln -sf /usr/share/backgrounds/default.png /usr/share/backgrounds/default.jxl
ln -sf /usr/share/backgrounds/default-dark.png /usr/share/backgrounds/default-dark.jxl