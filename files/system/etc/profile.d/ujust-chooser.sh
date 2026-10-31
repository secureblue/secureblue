# shellcheck shell=sh

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

if command -v fzf >/dev/null 2>&1; then
    unset JUST_CHOOSER
else
    export JUST_CHOOSER=/usr/bin/echo
fi
