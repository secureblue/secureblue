#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -oue pipefail

echo "Disabling all systemd-homed services"

# We intentionally don't mask the services, because
# some users may want to use it. But we disable it by default
# to reduce attack surface, since we don't use it by default.

# Note: systemd-homed-firstboot.service is already preset-disabled by default,
# but adding here just in case it's preset-enabled by default in the future.

systemctl disable systemd-homed-activate.service
systemctl disable systemd-homed-firstboot.service
systemctl disable systemd-homed.service
