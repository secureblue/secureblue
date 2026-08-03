#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
# SPDX-FileCopyrightText: Timothée Ravier <tim@siosm.fr>
#
# SPDX-License-Identifier: Apache-2.0 AND CC0-1.0

set -euxo pipefail

# Install composefs/UKI-specific packages.
# We replace systemd-boot with a signed version at a later stage.
dnf install -y fsverity-utils systemd-boot-unsigned efitools
# bootc >1.16.0 needed.
dnf upgrade -y --enablerepo=updates-testing --refresh bootc
# TODO: Install sbctl from our own copr for use by advanced users, see
# <https://github.com/secureblue/secureblue/issues/1917>.

# Remove rpm-ostree legacy files.
dnf remove -y \
    rpm-ostree \
    rpm-ostree-libs \
    gnome-software-rpm-ostree \
    plasma-discover-rpm-ostree
dnf clean all
rpm -e bootupd
rm -vrf "/usr/lib/bootupd"
rm -vrf "/usr/lib/ostree-boot"
rm -vrf "/usr/etc"

# Remove GRUB packages.
grub_packages=(
    "grub2-common"
    "grub2-efi-x64"
    "grub2-pc"
    "grub2-pc-modules"
    "grub2-tools"
    "grub2-tools-minimal"
)
if [[ "$(rpm -qa | grep -c grub2-efi-ia32)" -ne 0 ]]; then
    grub_packages+=("grub2-efi-ia32")
fi
rpm -e --nodeps "${grub_packages[@]}"

# Add kargs to bootc kargs.d; see uki.sh where we parse these for the UKI.
cat > "/usr/lib/bootc/kargs.d/10-rootfs.toml" << 'EOF'
kargs = [
  "rw",
  "rootflags=compress=zstd:1",
]
EOF
cat > "/usr/lib/bootc/kargs.d/10-plymouth.toml" << 'EOF'
kargs = [
  "quiet",
  "rhgb",
]
EOF
# Temporary. See: https://github.com/systemd/systemd/issues/40159 and
# https://github.com/systemd/systemd/issues/40485.
cat > "/usr/lib/bootc/kargs.d/20-tpm2-workaround.toml" << 'EOF'
kargs = [
  "rd.systemd.mask=systemd-tpm2-setup-early.service",
  "systemd.mask=systemd-tpm2-setup-early.service",
  "systemd.mask=systemd-tpm2-setup.service",
  "systemd.mask=systemd-pcrphase.service",
  "systemd.mask=systemd-pcrproduct.service",
]
EOF

# bootc installation configuration.
cat > "/usr/lib/bootc/install/80-rootfs.toml" << 'EOF'
# Default to btrfs
[install.filesystem.root]
type = "btrfs"
EOF
cat > "/usr/lib/bootc/install/90-install.toml" << 'EOF'
# Need systemd as the bootloader
[install]
bootloader = "systemd"
EOF

# bootc-specific dracut configuration.
cat > "/usr/lib/dracut/dracut.conf.d/20-secureblue.conf" << 'EOF'
install_items+=" /usr/lib64/libhardened_malloc.so /usr/lib64/libno_rlimit_as.so "
EOF
cat > "/usr/lib/dracut/dracut.conf.d/20-bootc-composefs.conf" << 'EOF'
# Dracut will always fail to set security.selinux xattrs at build time
# https://github.com/dracut-ng/dracut-ng/issues/1561
export DRACUT_NO_XATTR=1

# Enable composefs backend in dracut
add_dracutmodules+=" bootc "

# Include systemd's hwdb
# See: https://github.com/systemd/systemd/issues/40159
# See: https://github.com/systemd/systemd/issues/40485
install_items+=" /etc/udev/hwdb.bin "
EOF
cat > "/usr/lib/dracut/dracut.conf.d/20-omit-modules.conf" << 'EOF'
# Remove more dracut modules to reduce the size of the initramfs.
omit_dracutmodules+=" fips fips-crypto-policies lunmask lvm memstrack modsign nss-softokn "
EOF
cat > "/usr/lib/dracut/dracut.conf.d/59-altfiles.conf" << 'EOF'
# https://issues.redhat.com/browse/RHEL-49590
# On image mode systems we use nss-altfiles for passwd and group,
# this makes sure dracut uses them which also fixes kdump writing to NFS.
install_items+=" /usr/lib/passwd /usr/lib/group "
EOF

# Set systemd presets.
cat > "/usr/lib/systemd/system-preset/30-secureblue-uki.preset" << 'EOF'
enable bootc-status.service
enable bootc-upgrade.timer
EOF
systemctl preset-all --preset-mode=enable-only

# Prepare folders in /boot
mkdir -p /boot/EFI/Linux
