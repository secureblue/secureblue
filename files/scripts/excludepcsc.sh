#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -oue pipefail

sed -i '/^add_dracutmodules+=" .* "/s/ pcsc / /' /usr/lib/dracut/dracut.conf.d/90-ublue-luks.conf
