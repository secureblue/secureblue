#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

echo "Disabling the location service"

# Systemd service
systemctl disable geoclue.service
systemctl mask geoclue.service

# Append "Hidden=true" to prevent GeoClue Demo Agent from auto-starting
echo "Hidden=true" >> /etc/xdg/autostart/geoclue-demo-agent.desktop
