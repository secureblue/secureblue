#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

sed -i 's/Do not turn off your computer/Press Q to boot existing deployment/' /usr/share/plymouth/themes/bgrt/bgrt.plymouth
sed -i 's/Installing Updates/Downloading Updates/' /usr/share/plymouth/themes/bgrt/bgrt.plymouth