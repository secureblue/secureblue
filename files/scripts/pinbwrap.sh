#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# This is a hotfix for a regression introduced by changes in bwrap 0.12
# that need to be permanently resolved via changes in Trivalent

BWRAP_VERSION="$(dnf5 repoquery \
    --arch "${OS_ARCH}" \
    --queryformat '%{name}-%{version}-%{release}.%{arch}' \
    'bubblewrap-0.11.0-4.fc44'
)"

dnf5 -y install --allowerasing "${BWRAP_VERSION}"