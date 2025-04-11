#!/usr/bin/env bash

# Copyright 2025 Universal Blue
# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

set -oue pipefail

KERNEL_VERSION="$(rpm -q "kernel" --queryformat '%{VERSION}-%{RELEASE}.%{ARCH}')"
ZFS_MINOR_VERSION="2.3"

curl "https://api.github.com/repos/openzfs/zfs/releases" -o data.json
ZFS_VERSION=$(jq -r --arg ZMV "zfs-${ZFS_MINOR_VERSION}" '[ .[] | select(.prerelease==false and .draft==false) | select(.tag_name | startswith($ZMV))][0].tag_name' data.json|cut -f2- -d-)
echo "ZFS_VERSION==$ZFS_VERSION"

dnf install -y "kernel-devel-matched-$(rpm -q 'kernel' --queryformat '%{VERSION}')"
dnf install -y autoconf automake gcc pv akmods mock libtirpc-devel libblkid-devel libuuid-devel libudev-devel openssl-devel libaio-devel libattr-devel elfutils-libelf-devel python3-devel libffi-devel libcurl-devel ncompress python3-setuptools


### BUILD zfs
echo "getting zfs-${ZFS_VERSION}.tar.gz"
curl -L -O "https://github.com/openzfs/zfs/releases/download/zfs-${ZFS_VERSION}/zfs-${ZFS_VERSION}.tar.gz"
curl -L -O "https://github.com/openzfs/zfs/releases/download/zfs-${ZFS_VERSION}/zfs-${ZFS_VERSION}.tar.gz.asc"
curl -L -O "https://github.com/openzfs/zfs/releases/download/zfs-${ZFS_VERSION}/zfs-${ZFS_VERSION}.sha256.asc"

echo "Import key"
# https://openzfs.github.io/openzfs-docs/Project%20and%20Community/Signing%20Keys.html
gpg --yes --keyserver keyserver.ubuntu.com --recv D4598027

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


dnf install -y ./*.rpm
cd ..

./signmodules.sh "zfs"

echo '

omit_dracutmodules+=" zfs "

' > /usr/lib/dracut/dracut.conf.d/99-omit-zfs.conf

depmod -a -v "${KERNEL_VERSION}"

rm -f /etc/dnf/protected.d/sudo.conf

dnf remove -y sudo autoconf automake mock 

systemctl disable akmods-keygen@akmods-keygen.service
systemctl disable akmods-keygen.target

