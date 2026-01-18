#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -oue pipefail

rm -f /etc/yum.repos.d/negativo17-fedora-nvidia.repo
rm -f /etc/yum.repos.d/eyecantcu-supergfxctl.repo
rm -f /etc/yum.repos.d/_copr_ublue-os-akmods.repo
rm -f /etc/yum.repos.d/_copr:copr.fedorainfracloud.org:phracek:PyCharm.repo
rm -f /etc/yum.repos.d/google-chrome.repo
rm -f /etc/yum.repos.d/rpmfusion-nonfree-nvidia-driver.repo
rm -f /etc/yum.repos.d/rpmfusion-nonfree-steam.repo
rm -f /etc/yum.repos.d/rpmfusion-nonfree-nvidia-driver.repo.rpmsave
rm -f /etc/yum.repos.d/rpmfusion-nonfree-steam.repo.rpmsave
rm -f /etc/yum.repos.d/fedora-cisco-openh264.repo
rm -f /etc/yum.repos.d/fedora-nvidia-580.repo