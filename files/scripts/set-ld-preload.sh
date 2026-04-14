#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# Make ld.so.preload readable only by root, so user processes can override
# hardened_malloc by resetting LD_PRELOAD.
umask 077
echo 'libhardened_malloc.so' > /etc/ld.so.preload
