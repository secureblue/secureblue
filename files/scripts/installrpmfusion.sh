#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

rpm -q rpmfusion-free-release || rpm-ostree install https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-${OS_VERSION}.noarch.rpm
rpm -q rpmfusion-nonfree-release || rpm-ostree install https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-${OS_VERSION}.noarch.rpm