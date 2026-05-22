#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

sed -i \
    -e 's/^Title=Installing Updates/Title=Downloading Updates/' \
    -e 's/^SubTitle=Do not turn off your computer.*/SubTitle=Press Q to boot existing deployment/' \
    /usr/share/plymouth/themes/bgrt/bgrt.plymouth
