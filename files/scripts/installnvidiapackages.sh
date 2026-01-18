#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -oue pipefail


nvidia_packages_list=('libva-nvidia-driver' 'nvidia-container-toolkit')

is_desktop="false"
[[ "$IMAGE_NAME" != *"securecore"* && "$IMAGE_NAME" != *"iot"* ]] && is_desktop="true"
nvidia_packages_list+=(
  'nvidia-driver-cuda'
)    
if [[ "$is_desktop" == "true" ]]; then
    nvidia_packages_list+=(
        'libnvidia-fbc'
        'nvidia-driver' 
        'nvidia-modprobe' 
        'nvidia-persistenced' 
        'nvidia-settings'
    )
fi

curl -fLsS --retry 5 https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo \
    -o /etc/yum.repos.d/nvidia-container-toolkit.repo
sed -i -e 's/^gpgcheck=0/gpgcheck=1/' -e 's/^enabled=0.*/enabled=1/' /etc/yum.repos.d/nvidia-container-toolkit.repo

if [[ "$IMAGE_NAME" == *"open"* ]]; then
    curl -fLsS --retry 5 https://negativo17.org/repos/fedora-nvidia.repo -o /etc/yum.repos.d/negativo17-fedora-nvidia.repo
    sed -i 's/^enabled=0.*/enabled=1\npriority=90/' /etc/yum.repos.d/negativo17-fedora-nvidia.repo
else
    curl -fLsS --retry 5 -o /etc/yum.repos.d/fedora-nvidia-580.repo https://negativo17.org/repos/fedora-nvidia-580.repo
    sed -i '/^enabled=1/a\priority=90' /etc/yum.repos.d/fedora-nvidia-580.repo
fi
# required for rpm-ostree to function properly
# shellcheck disable=SC2068
dnf install -y --setopt=install_weak_deps=False ${nvidia_packages_list[@]}

kmod_version=$(rpm -qa | grep akmod-nvidia | awk -F':' '{print $(NF)}' | awk -F'-' '{print $(NF-1)}')
negativo_version=$(rpm -qa | grep nvidia-modprobe | awk -F':' '{print $(NF)}' | awk -F'-' '{print $(NF-1)}')

echo "kmod_version: ${kmod_version}"
echo "negativo_version: ${negativo_version}"
if [[ "$kmod_version" != "$negativo_version" ]]; then
    echo "Version mismatch!"
    exit 1
fi

curl -fLsS --retry 5 https://raw.githubusercontent.com/NVIDIA/dgx-selinux/b988ea65e7b43009a705eb5e5d7e94048f916734/bin/RHEL9/nvidia-container.pp \
    -o nvidia-container.pp
semodule -i nvidia-container.pp

rm -f nvidia-container.pp
rm -f /etc/yum.repos.d/negativo17-fedora-nvidia.repo
rm -f /etc/yum.repos.d/nvidia-container-toolkit.repo
