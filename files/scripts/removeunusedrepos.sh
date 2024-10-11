#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

rm /etc/yum.repos.d/negativo17-fedora-nvidia.repo
rm /etc/yum.repos.d/negativo17-fedora-multimedia.repo
rm /etc/yum.repos.d/eyecantcu-supergfxctl.repo
rm /etc/yum.repos.d/_copr_ublue-os-akmods.repo
rm /etc/yum.repos.d/nvidia-container-toolkit.repo
