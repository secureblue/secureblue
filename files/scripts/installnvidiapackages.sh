#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail


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

if [[ "$IMAGE_NAME" == *open* ]]; then
    nvidia_repo='fedora-nvidia'
else
    nvidia_repo='fedora-nvidia-580'
fi

dnf install -y --setopt=install_weak_deps=False \
    --enable-repo="${nvidia_repo}" \
    --enable-repo='nvidia-container-toolkit' \
    --disable-repo='fedora-multimedia' \
    "${nvidia_packages_list[@]}"

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
