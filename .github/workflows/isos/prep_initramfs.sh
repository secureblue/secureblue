#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

ldconfig
sed -i '/^install squashfs /d' /usr/lib/modprobe.d/secureblue.conf
echo 'install squashfs /sbin/modprobe --ignore-install squashfs' > /etc/modprobe.d/zz-squashfs-override.conf
echo 'install_items+=" /usr/lib64/libno_rlimit_as.so /etc/ld.so.cache /etc/modprobe.d/zz-squashfs-override.conf "' > /etc/dracut.conf.d/libs.conf

cat >> /usr/share/cockpit/branding/fedora/branding.css << 'EOF'
.anaconda {
    .pf-v6-c-form__section:has(#anaconda-screen-accounts-root-account-enable-root-account) {
        /* Hide the whole section with "Enable root account". Might be not as reliable as it seems to be */
        display: none;
    }
}
EOF