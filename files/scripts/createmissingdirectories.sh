#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -oue pipefail

# https://bugzilla.redhat.com/show_bug.cgi?id=2259249
mkdir -p /var/log/usbguard
