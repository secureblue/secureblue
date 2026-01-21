#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -oue pipefail

# Reference: https://gist.github.com/ok-ryoko/1ff42a805d496cb1ca22e5cdf6ddefb0#usrbinchage

whitelist=(
    # Required for nvidia closed driver images
    "/usr/bin/nvidia-modprobe"
    # https://gitlab.freedesktop.org/polkit/polkit/-/issues/168
    "/usr/lib/polkit-1/polkit-agent-helper-1"
    # https://github.com/secureblue/secureblue/issues/119
    # Required for hardened_malloc to be used by suid-root processes
    "/usr/lib64/libhardened_malloc-light.so"
    "/usr/lib64/libhardened_malloc-pkey.so"
    "/usr/lib64/libhardened_malloc.so"
    "/usr/lib64/glibc-hwcaps/x86-64/libhardened_malloc-light.so"
    "/usr/lib64/glibc-hwcaps/x86-64/libhardened_malloc-pkey.so"
    "/usr/lib64/glibc-hwcaps/x86-64/libhardened_malloc.so"
    "/usr/lib64/glibc-hwcaps/x86-64-v2/libhardened_malloc-light.so"
    "/usr/lib64/glibc-hwcaps/x86-64-v2/libhardened_malloc-pkey.so"
    "/usr/lib64/glibc-hwcaps/x86-64-v2/libhardened_malloc.so"
    "/usr/lib64/glibc-hwcaps/x86-64-v3/libhardened_malloc-light.so"
    "/usr/lib64/glibc-hwcaps/x86-64-v3/libhardened_malloc-pkey.so"
    "/usr/lib64/glibc-hwcaps/x86-64-v3/libhardened_malloc.so"
    "/usr/lib64/glibc-hwcaps/x86-64-v4/libhardened_malloc-light.so"
    "/usr/lib64/glibc-hwcaps/x86-64-v4/libhardened_malloc-pkey.so"
    "/usr/lib64/glibc-hwcaps/x86-64-v4/libhardened_malloc.so"
    "/usr/lib64/libno_rlimit_as.so"
)


is_in_whitelist() {
    local binary="$1"
    for allowed_binary in "${whitelist[@]}"; do
        if [ "$binary" = "$allowed_binary" ]; then
            return 0
        fi
    done
    return 1
}

find /usr -type f -perm /4000 |
    while IFS= read -r binary; do
        if ! is_in_whitelist "$binary"; then
            echo "Removing SUID bit from $binary"
            chmod u-s "$binary"
            echo "Removed SUID bit from $binary"
        fi
    done

find /usr -type f -perm /2000 |
    while IFS= read -r binary; do
        if ! is_in_whitelist "$binary"; then
            echo "Removing SGID bit from $binary"
            chmod g-s "$binary"
            echo "Removed SGID bit from $binary"
        fi
    done

rm -f /usr/bin/chsh
rm -f /usr/bin/chfn
rm -f /usr/bin/pkexec
rm -f /usr/bin/sudo
rm -f /usr/bin/su

set_caps_if_present() {
    local caps="$1"
    local binary_path="$2"
    if [ -f "$binary_path" ]; then
        echo "Setting caps $caps on $binary_path"
        setcap "$caps" "$binary_path"
        echo "Set caps $caps on $binary_path"
    fi
}

set_caps_if_present "cap_dac_read_search,cap_audit_write=ep" "/usr/bin/chage"
set_caps_if_present "cap_sys_admin=ep" "/usr/bin/fusermount3"
set_caps_if_present "cap_dac_read_search,cap_audit_write=ep" "/usr/sbin/unix_chkpwd"

# spice-client-glib-usb-acl-helper drops all capabilities except CAP_FOWNER:
# https://gitlab.freedesktop.org/spice/spice-gtk/-/blob/7a2779182b003ec5e8192dc5186f0b1c3eb8e831/src/spice-client-glib-usb-acl-helper.c#L304
set_caps_if_present "cap_fowner=ep" "/usr/libexec/spice-gtk-$(uname -m)/spice-client-glib-usb-acl-helper"

# The below capabilities are expected by these QEMU-related executables but do
# not seem to be needed for ordinary libvirt/QEMU/KVM usage. They are left
# commented out for reference in case we later determine that the capabilities
# should be added back.

# Mounting and unmounting requires CAP_SYS_ADMIN:
# set_caps_if_present "cap_sys_admin=ep" "/usr/bin/fusermount-glusterfs"

# qemu-bridge-helper drops all capabilities except CAP_NET_ADMIN:
# https://gitlab.com/qemu-project/qemu/-/blob/667e1fff878326c35c7f5146072e60a63a9a41c8/qemu-bridge-helper.c#L252
# set_caps_if_present "cap_net_admin=ep" "/usr/libexec/qemu-bridge-helper"
