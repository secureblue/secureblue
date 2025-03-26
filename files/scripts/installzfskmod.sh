#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

dnf install -y https://zfsonlinux.org/fedora/zfs-release-2-6$(rpm --eval "%{dist}").noarch.rpm
dnf install -y kernel-devel-$(uname -r | awk -F'-' '{print $1}')
dnf install -y zfs

./signmodules.sh "zfs"

echo '

omit_dracutmodules+=" zfs "

' > /usr/lib/dracut/dracut.conf.d/99-omit-zfs.conf


KERNEL_VERSION="$(rpm -q "kernel" --queryformat '%{VERSION}-%{RELEASE}.%{ARCH}')"
depmod -a -v "${KERNEL_VERSION}"