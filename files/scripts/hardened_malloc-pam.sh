#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

sed -i -e '$a\LD_PRELOAD DEFAULT="libhardened_malloc.so libno_rlimit_as.so"' -e '/^LD_PRELOAD[[:space:]]/d' /etc/security/pam_env.conf
