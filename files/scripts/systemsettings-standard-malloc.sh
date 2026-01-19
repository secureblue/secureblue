#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# Unset LD_PRELOAD in all invocations of systemsettings in .desktop files
sed -Ei 's/^Exec=systemsettings( .*)?$/Exec=env LD_PRELOAD= systemsettings\1/' /usr/share/applications/*.desktop
