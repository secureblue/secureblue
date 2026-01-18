#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025 Universal Blue
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -oue pipefail

IMAGE_PRETTY_NAME="secureblue"
IMAGE_LIKE="fedora"
HOME_URL="https://github.com/secureblue/secureblue"
DOCUMENTATION_URL="https://github.com/secureblue/secureblue/tree/live/docs"
SUPPORT_URL="https://github.com/secureblue/secureblue/issues"
BUG_SUPPORT_URL="https://github.com/secureblue/secureblue/issues"


sed -i --sandbox "s|^VARIANT_ID=.*|VARIANT_ID=$IMAGE_NAME|" /usr/lib/os-release
sed -i --sandbox "s|^PRETTY_NAME=.*|PRETTY_NAME=\"${IMAGE_PRETTY_NAME} (powered by Fedora Atomic)\"|" /usr/lib/os-release
sed -i --sandbox "s|^NAME=.*|NAME=\"$IMAGE_PRETTY_NAME\"|" /usr/lib/os-release
sed -i --sandbox "s|^HOME_URL=.*|HOME_URL=\"$HOME_URL\"|" /usr/lib/os-release
sed -i --sandbox "s|^DOCUMENTATION_URL=.*|DOCUMENTATION_URL=\"$DOCUMENTATION_URL\"|" /usr/lib/os-release
sed -i --sandbox "s|^SUPPORT_URL=.*|SUPPORT_URL=\"$SUPPORT_URL\"|" /usr/lib/os-release
sed -i --sandbox "s|^BUG_REPORT_URL=.*|BUG_REPORT_URL=\"$BUG_SUPPORT_URL\"|" /usr/lib/os-release
sed -i --sandbox "s|^CPE_NAME=\"cpe:/o:fedoraproject:fedora|CPE_NAME=\"cpe:/o:secureblue:${IMAGE_PRETTY_NAME,}|" /usr/lib/os-release
sed -i --sandbox "s|^DEFAULT_HOSTNAME=.*|DEFAULT_HOSTNAME=\"${IMAGE_PRETTY_NAME,}\"|" /usr/lib/os-release
sed -i --sandbox "s|^ID=fedora|ID=${IMAGE_PRETTY_NAME,}\nID_LIKE=\"${IMAGE_LIKE}\"|" /usr/lib/os-release
sed -Ei '/^REDHAT_(BUGZILLA|SUPPORT)_PRODUCT(_VERSION)?=/d' /usr/lib/os-release

# Added in systemd 249.
# https://www.freedesktop.org/software/systemd/man/latest/os-release.html#IMAGE_ID=
sed -i --sandbox '$a\IMAGE_ID='"\"${IMAGE_NAME}\"" /usr/lib/os-release

# Fix issues caused by ID no longer being fedora
sed -i 's/^EFIDIR=.*/EFIDIR="fedora"/' /usr/sbin/grub2-switch-to-blscfg
