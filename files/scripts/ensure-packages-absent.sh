#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

packages=(
    NetworkManager-fortisslvpn
    NetworkManager-iodine
    NetworkManager-l2tp
    NetworkManager-libreswan
    NetworkManager-pptp
    NetworkManager-ssh
    NetworkManager-sstp
    NetworkManager-strongswan
    NetworkManager-vpnc
    blender
    plocate
    sushi
)

for pkg in "${packages[@]}"; do
    if rpm -q "${pkg}" &>/dev/null; then
        echo "${pkg} found. Exiting..."
        exit 1
    fi
done

if command -v sudo &>/dev/null; then
    echo "sudo found. Exiting..."
    exit 1
fi
