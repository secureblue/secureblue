#!/usr/bin/env bash

set -oue pipefail

nvidia_packages_list=('nvidia-container-toolkit' 'nvidia-driver-cuda')
if [[ "$IMAGE_NAME" != *"securecore"* ]]; then
    nvidia_packages_list+=('libnvidia-fbc' 'libva-nvidia-driver' 'nvidia-driver' 'nvidia-modprobe' 'nvidia-persistenced' 'nvidia-settings')
fi

curl -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo \
    -o /etc/yum.repos.d/nvidia-container-toolkit.repo
sed -i "s@gpgcheck=0@gpgcheck=1@" /etc/yum.repos.d/nvidia-container-toolkit.repo

curl -L https://negativo17.org/repos/fedora-nvidia.repo -o /etc/yum.repos.d/negativo17-fedora-nvidia.repo


sed -i '0,/enabled=0/{s/enabled=0/enabled=1/}' /etc/yum.repos.d/nvidia-container-toolkit.repo
sed -i '0,/enabled=0/{s/enabled=0/enabled=1\npriority=90/}' /etc/yum.repos.d/negativo17-fedora-nvidia.repo
# required for rpm-ostree to function properly
# shellcheck disable=SC2068
rpm-ostree install ${nvidia_packages_list[@]}

kmod_version=$(rpm -qa | grep akmod-nvidia | awk -F':' '{print $(NF)}' | awk -F'-' '{print $(NF-1)}')
negativo_version=$(rpm -qa | grep nvidia-modprobe | awk -F':' '{print $(NF)}' | awk -F'-' '{print $(NF-1)}')

echo "kmod_version: ${kmod_version}"
echo "negativo_version: ${negativo_version}"
if [[ "$kmod_version" != "$negativo_version" ]]; then
    echo "Version mismatch!"
    exit 1
fi

curl -L https://raw.githubusercontent.com/NVIDIA/dgx-selinux/master/bin/RHEL9/nvidia-container.pp \
    -o nvidia-container.pp
semodule -i nvidia-container.pp

rm -f nvidia-container.pp
rm -f /etc/yum.repos.d/negativo17-fedora-nvidia.repo
rm -f /etc/yum.repos.d/nvidia-container-toolkit.repo
