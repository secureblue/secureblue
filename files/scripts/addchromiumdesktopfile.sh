#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -oue pipefail

sed -i 's/org.mozilla.firefox/trivalent/' /usr/share/wayfire/wf-shell.ini
