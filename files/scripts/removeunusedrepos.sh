#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Remove RPMFusion repos (secureblue uses Negativo instead) and some other unused repos

set -euo pipefail

repos_to_remove=(
    eyecantcu-supergfxctl.repo
    _copr_ublue-os-akmods.repo
    _copr:copr.fedorainfracloud.org:phracek:PyCharm.repo
    google-chrome.repo
    fedora-cisco-openh264.repo
    rpmfusion-nonfree-nvidia-driver.repo
    rpmfusion-nonfree-steam.repo
    rpmfusion-nonfree-nvidia-driver.repo.rpmsave
    rpmfusion-nonfree-steam.repo.rpmsave
)

for repo in "${repos_to_remove[@]}"; do
    rm -f "/usr/share/dnf5/repos.d/${repo}" "/etc/yum.repos.d/${repo}"
done
