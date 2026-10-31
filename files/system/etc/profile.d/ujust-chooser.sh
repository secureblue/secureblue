# shellcheck shell=sh

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

if command -v fzf >/dev/null 2>&1; then
    export JUST_CHOOSER='/usr/bin/fzf --multi --preview "just --color always --show {}"'
else
    export JUST_CHOOSER=/usr/bin/echo
fi
