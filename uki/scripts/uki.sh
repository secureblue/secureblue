#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
# SPDX-FileCopyrightText: Timothée Ravier <tim@siosm.fr>
#
# SPDX-License-Identifier: Apache-2.0 AND CC0-1.0

set -euxo pipefail

target="/run/target"
output="/boot/EFI/Linux"
secrets="/run/secrets"

# Find the kernel version (needed for output filename)
kver=$(cd "${target}/usr/lib/modules" && echo *)

# Baseline ukify options
mkdir -p "${output}"
ukifyargs=(
    --measure
    --json pretty
    --output "${output}/${kver}.efi"
    --signtool sbsign
    --secureboot-private-key "${secrets}/secureboot_key"
    --secureboot-certificate "${secrets}/secureboot_crt"
)

# In future, `bootc container ukify` will compute the composefs digest, read
# kargs from kargs.d, and invoke ukify in one step. But the current
# implementation needs the kernel and initrd in the image, and we can't remove
# them later without changing the composefs hash, so we do it manually instead.
# See: https://github.com/bootc-dev/bootc/issues/2185.
# bootc container ukify --rootfs ${target} -- ${ukifyargs[@]}

# Compute the composefs digest from the mounted rootfs
digest="$(bootc container compute-composefs-digest "${target}")"

# For the cmdline, add the composefs digest and parse the kargs from kargs.d,
# which includes the kargs set in prepare-rootfs.sh. This is temporary, see
# above.
kargs_d=$(
    grep -rh '"' "${target}/usr/lib/bootc/kargs.d" |
    grep -v '^#' | sed 's/,$//' | tr -d ' "' | tr '\n' ' '
)
printf "composefs=%s %s\n" "${digest}" "${kargs_d}" > /etc/kernel/cmdline

# Generate and sign the UKI with the digest embedded
ukify build \
    --linux "/vmlinuz" \
    --initrd "/initramfs" \
    --uname="${kver}" \
    --cmdline "@/etc/kernel/cmdline" \
    --os-release "@${target}/usr/lib/os-release" \
    "${ukifyargs[@]}"
