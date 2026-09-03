#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail
shopt -s nullglob

dnf install -y --setopt=install_weak_deps=False gh rpm-sign
rpmkeys --import /usr/share/pki/rpm-gpg/RPM-GPG-KEY-terra44.gpg

sed -i 's/^enabled=0$/enabled=1/' /etc/yum.repos.d/terra.repo

# https://github.com/terrapkg/packages/issues/12949
check_local_rpm_provenance() {
    for terra_rpm in *.rpm; do
        cp "${terra_rpm}" "unsigned-${terra_rpm}"
        rpm --delsign "unsigned-${terra_rpm}"
        gh attestation verify "unsigned-${terra_rpm}" \
            --repo terrapkg/packages \
            --signer-workflow terrapkg/packages/.github/workflows/json-build.yml \
            --source-ref "refs/heads/f44"
        rm "unsigned-${terra_rpm}"
    done
}

dnf --best --repo=terra -y download --resolve \
    terra-release-mesa \
    terra-release-multimedia \
    terra-release-extras

check_local_rpm_provenance

dnf -y --setopt=localpkg_gpgcheck=True --setopt=install_weak_deps=False install ./*.rpm
rm ./*.rpm

rpmkeys --import /etc/pki/rpm-gpg/RPM-GPG-KEY-terra44-mesa \
    /etc/pki/rpm-gpg/RPM-GPG-KEY-terra44-multimedia \
    /etc/pki/rpm-gpg/RPM-GPG-KEY-terra44-extras

dnf --best --repo=terra-mesa -y download --resolve \
    mesa-dri-drivers \
    mesa-filesystem \
    mesa-libEGL \
    mesa-libGL \
    mesa-libgbm \
    mesa-vulkan-drivers
 
dnf --best --repo=terra-multimedia -y download --resolve \
    ffmpeg \
    libavcodec \
    libavdevice \
    libavfilter \
    libavformat \
    libavutil \
    libswresample \
    libswscale

dnf --best --repo=terra-extras -y download --resolve \
    unrar

check_local_rpm_provenance

dnf -y --setopt=localpkg_gpgcheck=True --setopt=install_weak_deps=False 'do' \
    --allowerasing \
    --action=remove \
        ffmpeg-free \
        libavcodec-free \
        libavdevice-free \
        libavfilter-free \
        libavformat-free \
        libavutil-free \
        libswresample-free \
        libswscale-free \
    --action=install ./*.rpm
rm ./*.rpm

dnf remove -y gh

sed -i -e 's/^enabled=1$/enabled=0/' \
    /etc/yum.repos.d/terra.repo \
    /etc/yum.repos.d/terra-mesa.repo \
    /etc/yum.repos.d/terra-multimedia.repo \
    /etc/yum.repos.d/terra-extras.repo
