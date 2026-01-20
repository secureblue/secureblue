#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -oue pipefail

LATEST_ANDROID_UDEV_RULES_COMMIT="e62577fade0e79a965edfff732b88f228266cb0b" # 20250525
curl -fLsS --retry 5 -O "https://github.com/M0Rf30/android-udev-rules/archive/${LATEST_ANDROID_UDEV_RULES_COMMIT}.tar.gz"
tar xvf "${LATEST_ANDROID_UDEV_RULES_COMMIT}.tar.gz" --strip-components=1

install -m 644 51-android.rules /etc/udev/rules.d/
mkdir -p /usr/lib/sysusers.d/
install -m 644 android-udev.conf /usr/lib/sysusers.d/.
