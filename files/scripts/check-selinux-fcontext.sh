#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

if grep -q '^/var/home ' /etc/selinux/targeted/contexts/files/file_contexts.subs_dist; then
    echo "Bad file context (aliasing /var/home) found in file_contexts.subs_dist."
    echo "This is a bug that we're still trying to track down."
    echo "Making build fail to ensure this doesn't silently slip through."
    exit 1
fi
