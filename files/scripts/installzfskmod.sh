#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025 Universal Blue
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -oue pipefail

KERNEL_VERSION="$(rpm -q "kernel" --queryformat '%{VERSION}-%{RELEASE}.%{ARCH}')"
ZFS_MINOR_VERSION="2.4"

curl -fLsS --retry 5 -o data.json "https://api.github.com/repos/openzfs/zfs/releases"
ZFS_VERSION=$(jq -r --arg ZMV "zfs-${ZFS_MINOR_VERSION}" '[ .[] | select(.prerelease==false and .draft==false) | select(.tag_name | startswith($ZMV))][0].tag_name' data.json|cut -f2- -d-)
echo "ZFS_VERSION==$ZFS_VERSION"

dnf install -y --setopt=install_weak_deps=False "kernel-devel-matched-$(rpm -q 'kernel' --queryformat '%{VERSION}')"
dnf install -y --setopt=install_weak_deps=False autoconf automake gcc pv akmods mock libunwind-devel pam-devel libatomic libtirpc-devel libblkid-devel libuuid-devel libudev-devel openssl-devel libaio-devel libattr-devel elfutils-libelf-devel python3-devel python3-cffi libffi-devel libcurl-devel ncompress python3-setuptools


### BUILD zfs
echo "getting zfs-${ZFS_VERSION}.tar.gz"
curl -fLsS --retry 5 \
    -O "https://github.com/openzfs/zfs/releases/download/zfs-${ZFS_VERSION}/zfs-${ZFS_VERSION}.tar.gz" \
    -O "https://github.com/openzfs/zfs/releases/download/zfs-${ZFS_VERSION}/zfs-${ZFS_VERSION}.tar.gz.asc" \
    -O "https://github.com/openzfs/zfs/releases/download/zfs-${ZFS_VERSION}/zfs-${ZFS_VERSION}.sha256.asc"

echo "Import key"
# https://openzfs.github.io/openzfs-docs/Project%20and%20Community/Signing%20Keys.html
curl -fLsS --retry 5 "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0xD4598027"| gpg --yes --import
curl -fLsS --retry 5 "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0xC6AF658B"| gpg --yes --import

echo "Verifying tar.gz signature"
if ! gpg --verify "zfs-${ZFS_VERSION}.tar.gz.asc" "zfs-${ZFS_VERSION}.tar.gz"
then
    echo "ZFS tarball signature verification FAILED! Exiting..."
    exit 1
fi

echo "Verifying checksum signature"
if ! gpg --verify "zfs-${ZFS_VERSION}.sha256.asc"
then
    echo "Checksum signature verification FAILED! Exiting..."
    exit 1
fi

echo "Verifying encrypted checksum"
if ! gpg --decrypt "zfs-${ZFS_VERSION}.sha256.asc" | sha256sum -c
then
    echo "Checksum verification FAILED! Exiting..."
    exit 1
fi

tar -z -x --no-same-owner --no-same-permissions -f "zfs-${ZFS_VERSION}.tar.gz"

cd "zfs-${ZFS_VERSION}"
# We want to exit if either A or B is false
# shellcheck disable=SC2015
./configure \
        -with-linux="/usr/src/kernels/${KERNEL_VERSION}/" \
        -with-linux-obj="/usr/src/kernels/${KERNEL_VERSION}/" \
    && make -j "$(nproc)" rpm-utils rpm-kmod \
    || { cat config.log; exit 1; }

rm ./*src.rpm
rm ./*devel*.rpm
rm ./*debug*.rpm
rm ./zfs-test*.rpm

dnf install -y --setopt=install_weak_deps=False ./*.rpm
cd ..

./signmodules.sh "zfs"

echo '

omit_dracutmodules+=" zfs "

' > /usr/lib/dracut/dracut.conf.d/99-omit-zfs.conf

depmod -a -v "${KERNEL_VERSION}"

rm -f /etc/dnf/protected.d/sudo.conf

dnf remove -y sudo autoconf automake mock

systemctl disable akmods-keygen@akmods-keygen.service
systemctl mask akmods-keygen@akmods-keygen.service
systemctl disable akmods-keygen.target
systemctl mask akmods-keygen.target
