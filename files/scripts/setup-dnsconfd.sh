#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# This is usually done by `dnsconfd config install`, which fails if
# NetworkManager.service is not running. We imitate this by:
# - installing /etc/NetworkManager/conf.d/dnsconfd.conf manually, which tells
#   NetworkManager to use com.redhat.dnsconfd instead of
#   org.freedesktop.resolve1, and
# - setting the permissions of /etc/resolv.conf manually here.
chown dnsconfd:root /etc/resolv.conf
