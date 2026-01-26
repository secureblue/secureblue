#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

echo '

# Nvidia modesetting support. Set to 0 or comment to disable kernel modesetting
# support. This must be disabled in case of SLI Mosaic.

options nvidia-drm modeset=1 fbdev=1

' > /usr/lib/modprobe.d/nvidia-modeset.conf

cp /usr/lib/modprobe.d/nvidia-modeset.conf /etc/modprobe.d/nvidia-modeset.conf