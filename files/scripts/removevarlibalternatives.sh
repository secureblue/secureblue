#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# For some reason this directory exists while building which leads to
# update-alternatives think it's the admindir; See logic:
# https://github.com/fedora-sysv/chkconfig/blob/d00ad17ee7a8b8ac4f28d01a7edf3a8ca0d88af4/alternatives.c#L1513-L1527
# It's empty and should be safe or even preferred to be remove so
# update-alternatives can work properly
rm -rf /var/lib/alternatives
