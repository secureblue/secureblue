#!/usr/bin/env bash

set -oue pipefail

# Install from Fedora
rpm-ostree install libopenjph

curl -Lo /etc/yum.repos.d/negativo17-fedora-multimedia.repo https://negativo17.org/repos/fedora-multimedia.repo
sed -i '0,/enabled=1/{s/enabled=1/enabled=1\npriority=90/}' /etc/yum.repos.d/negativo17-fedora-multimedia.repo

rpm-ostree override replace \
  --experimental \
  --from repo='fedora-multimedia' \
    libheif \
    libva \
    libva-intel-media-driver \
    intel-gmmlib \
    intel-vpl-gpu-rt \
    intel-mediasdk \
    mesa-dri-drivers \
    mesa-filesystem \
    mesa-libEGL \
    mesa-libGL \
    mesa-libgbm \
    mesa-libxatracker \
    mesa-va-drivers \
    mesa-vulkan-drivers \
    gstreamer1-plugin-libav \
    gstreamer1-plugin-vaapi \
    rar
