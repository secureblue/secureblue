#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

audit_results=$(ujust audit-secureblue --json --skip flatpak | jq -c '{name, description, status, notes}')

if diff 'expected-audit-silverblue-main-hardened.txt' <(echo "${audit_results}"); then
    echo 'Audit script output is as expected.'
else
    echo 'Audit script output differs from expected output.'
    exit 1
fi
