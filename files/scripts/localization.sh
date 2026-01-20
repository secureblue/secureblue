#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

cd ../po
for po_file in */*.po; do
    lang_code=$(dirname -- "$po_file")
    mo_filename=$(basename -- "$po_file" | sed 's/\.po$/.mo/')
    msgfmt -o /usr/share/locale/"$lang_code"/LC_MESSAGES/"$mo_filename" -- "$po_file"
done
