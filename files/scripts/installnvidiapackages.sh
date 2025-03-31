#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

find /tmp/rpms

nvidia_packages_list=('/tmp/rpms/kmods/kmod-nvidia*.rpm' 'nvidia-container-toolkit' 'nvidia-driver-cuda')

if [[ "$IMAGE_NAME" == *"securecore"* ]]; then
    nvidia_config_rpm_location='/tmp/rpms/ucore/ublue-os-ucore-nvidia*.rpm'
else
    nvidia_config_rpm_location='/tmp/rpms/ublue-os/ublue-os-nvidia*.rpm'
    nvidia_packages_list+=('libnvidia-fbc' 'libva-nvidia-driver' 'nvidia-driver' 'nvidia-modprobe' 'nvidia-persistenced' 'nvidia-settings')
fi

if [ ! -f /etc/yum.repos.d/negativo17-fedora-nvidia.repo ]; then
    curl -L https://negativo17.org/repos/fedora-nvidia.repo -o /etc/yum.repos.d/negativo17-fedora-nvidia.repo
fi

# required for rpm-ostree to function properly
# shellcheck disable=SC2086
rpm-ostree install $nvidia_config_rpm_location
sed -i '0,/enabled=0/{s/enabled=0/enabled=1/}' /etc/yum.repos.d/nvidia-container-toolkit.repo
sed -i '0,/enabled=0/{s/enabled=0/enabled=1\npriority=90/}' /etc/yum.repos.d/negativo17-fedora-nvidia.repo
# required for rpm-ostree to function properly
# shellcheck disable=SC2068
rpm-ostree install ${nvidia_packages_list[@]}

kmod_version=$(find /tmp/rpms/kmods -maxdepth 1 -name 'kmod-nvidia*.rpm' | awk -F'-' '{print $(NF-1)}')
negativo_version=$(rpm -qa | grep nvidia-modprobe | awk -F':' '{print $(NF)}' | awk -F'-' '{print $(NF-1)}')

echo "kmod_version: ${kmod_version}"
echo "negativo_version: ${negativo_version}"
if [[ "$kmod_version" != "$negativo_version" ]]; then
    echo "Version mismatch!"
    exit 1
fi
