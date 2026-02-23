#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

if [[ "$OS_ARCH" == 'x86_64' ]]; then
    echo 'OPTIONS="-F1 -r"' > /etc/sysconfig/chronyd
else
    echo 'OPTIONS="-F2 -r"' > /etc/sysconfig/chronyd
fi
