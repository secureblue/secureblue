#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

echo "Disabling and masking libvirt monolithic daemon..."

systemctl disable libvirtd.service
systemctl mask libvirtd.service

for socket in libvirtd{,-ro,-admin,-tcp,-tls}.socket; do
    systemctl disable "$socket"
    systemctl mask "$socket"
done
