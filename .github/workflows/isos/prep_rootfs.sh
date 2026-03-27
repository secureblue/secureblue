#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

sed -i '/^install squashfs \/bin\/false$/d' /usr/lib/modprobe.d/secureblue.conf

systemctl disable bootloader-update.service
systemctl disable rpm-ostree-countme.service

dnf remove -y google-noto-fonts-all homebrew
dnf install -y secureblue-logos
dnf install -y anaconda-live libblockdev-btrfs 

systemctl disable --global secureblue-flatpak-setup.service
systemctl disable --global secureblue-flatpak-setup.timer

cat <<EOF >>/etc/anaconda/conf.d/anaconda.conf
[User Interface]
hidden_spokes =
    PasswordSpoke
password_policies = 
        root (quality 100, length 15)
        user (quality 50, length 15)
        luks (quality 100, length 20)
hidden_webui_pages =
    root-password
EOF

rm -f /usr/share/applications/org.mozilla.Firefox.desktop
rm -f /usr/share/applications/org.mozilla.firefox.desktop
rm -f /usr/share/applications/firefox.desktop
rm -f /usr/share/applications/firefox-wayland.desktop
rm -f /usr/share/applications/firefox-x11.desktop
