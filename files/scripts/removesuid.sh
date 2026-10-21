#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# Reference: https://gist.github.com/ok-ryoko/1ff42a805d496cb1ca22e5cdf6ddefb0

ignore_setuid_list=(
    # Required for nvidia closed driver images
    # https://github.com/NVIDIA/nvidia-modprobe/issues/12
    "/usr/bin/nvidia-modprobe"
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

should_remove_setuid() {
    local binary="$1"
    local allowed_binary
    for allowed_binary in "${ignore_setuid_list[@]}"; do
        if [[ "${binary}" == "${allowed_binary}" ]]; then
            return 1
        fi
    done
}

find /usr -type f -perm /6000 -print0 | while IFS= read -r -d '' binary; do
    if should_remove_setuid "${binary}"; then
        echo "Removing setuid/setgid bits from ${binary}"
        chmod ug-s "${binary}"
    fi
done

rm -f /usr/bin/chsh /usr/bin/chfn /usr/bin/pkexec /usr/bin/sudo /usr/bin/su

set_caps_if_present() {
    local caps="$1"
    local binary_path="$2"
    if [[ -f "${binary_path}" ]]; then
        echo "Setting caps ${caps} on ${binary_path}"
        setcap "${caps}" "${binary_path}"
        echo "Set caps ${caps} on ${binary_path}"
    fi
}

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
