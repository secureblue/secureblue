#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euxo pipefail

kver=$(cd "/usr/lib/modules" && echo *)

dracut \
    --verbose \
    --kver "${kver}" \
    --force \
    --install "/etc/passwd /etc/group" \
    --no-hostonly \
    --reproducible \
    "/initramfs"
