#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

sed -i '/^install squashfs \/bin\/false$/d' /usr/lib/modprobe.d/secureblue.conf

systemctl disable bootloader-update.service
systemctl disable rpm-ostree-countme.service

dnf remove -y google-noto-fonts-all homebrew
dnf install -y fedora-logos secureblue-logos
dnf install -y anaconda-live libblockdev-btrfs
dnf reinstall -y polkit 