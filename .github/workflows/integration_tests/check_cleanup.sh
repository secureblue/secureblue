#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

SERVICE_NAME="securebluecleanup.service"
if ! systemctl is-enabled --quiet "$SERVICE_NAME"; then
    echo "Error: $SERVICE_NAME is in a disabled state."
    exit 1
else 
    echo "$SERVICE_NAME is enabled."
fi

if systemctl is-failed --quiet "$SERVICE_NAME"; then
    echo "Error: $SERVICE_NAME is in a failed state."
    exit 1
else
    echo "$SERVICE_NAME succeeded."
fi