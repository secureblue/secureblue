#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

KERNEL_VERSION="$(rpm -q "kernel" --queryformat '%{VERSION}-%{RELEASE}.%{ARCH}')"
ZFS_MINOR_VERSION="2.3"

curl "https://api.github.com/repos/openzfs/zfs/releases" -o data.json
ZFS_VERSION=$(jq -r --arg ZMV "zfs-${ZFS_MINOR_VERSION}" '[ .[] | select(.prerelease==false and .draft==false) | select(.tag_name | startswith($ZMV))][0].tag_name' data.json|cut -f2- -d-)
echo "ZFS_VERSION==$ZFS_VERSION"


dnf install -y libtirpc-devel libblkid-devel libuuid-devel libudev-devel openssl-devel libaio-devel libattr-devel elfutils-libelf-devel python3-devel libffi-devel libcurl-devel ncompress python3-setuptools

### BUILD zfs
echo "getting zfs-${ZFS_VERSION}.tar.gz"
curl -L -O "https://github.com/openzfs/zfs/releases/download/zfs-${ZFS_VERSION}/zfs-${ZFS_VERSION}.tar.gz"
curl -L -O "https://github.com/openzfs/zfs/releases/download/zfs-${ZFS_VERSION}/zfs-${ZFS_VERSION}.tar.gz.asc"
curl -L -O "https://github.com/openzfs/zfs/releases/download/zfs-${ZFS_VERSION}/zfs-${ZFS_VERSION}.sha256.asc"

echo "Import key"
# https://openzfs.github.io/openzfs-docs/Project%20and%20Community/Signing%20Keys.html
gpg --yes --keyserver keyserver.ubuntu.com --recv D4598027

echo "Verifying tar.gz signature"
gpg --verify "zfs-${ZFS_VERSION}.tar.gz.asc" "zfs-${ZFS_VERSION}.tar.gz"
if [ $? -ne 0 ]; then
    echo "ZFS tarball signature verification FAILED! Exiting..."
    exit 1
fi

echo "Verifying checksum signature"
gpg --verify "zfs-${ZFS_VERSION}.sha256.asc"
if [ $? -ne 0 ]; then
    echo "Checksum signature verification FAILED! Exiting..."
    exit 1
fi

echo "Verifying encrypted checksum"
gpg --decrypt "zfs-${ZFS_VERSION}.sha256.asc" | sha256sum -c
if [ $? -ne 0 ]; then
    echo "Checksum verification FAILED! Exiting..."
    exit 1
fi

tar -z -x --no-same-owner --no-same-permissions -f zfs-${ZFS_VERSION}.tar.gz

./configure \
        -with-linux=/usr/src/kernels/${KERNEL_VERSION}/ \
        -with-linux-obj=/usr/src/kernels/${KERNEL_VERSION}/ \
    && make -j $(nproc) rpm-utils rpm-kmod \
    || (cat config.log && exit 1)

dnf install -y ./kmod-zfs-*.rpm


./signmodules.sh "zfs"

echo '

omit_dracutmodules+=" zfs "

' > /usr/lib/dracut/dracut.conf.d/99-omit-zfs.conf


depmod -a -v "${KERNEL_VERSION}"