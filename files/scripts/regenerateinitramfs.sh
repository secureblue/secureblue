#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail
shopt -s nullglob

# Set dracut log levels using temporary configuration file.
# This avoids logging messages to the system journal, which can significantly
# impact performance in the default configuration.
tmp_conf_file=$(mktemp '/etc/dracut.conf.d/zzz-loglevels-XXXXXXXXXX.conf')
cat >"${tmp_conf_file}" <<'EOF'
stdloglvl=4
sysloglvl=0
kmsgloglvl=0
fileloglvl=0
EOF
trap 'rm -f -- "${tmp_conf_file}"' EXIT

# Exclude file that sets LD_PRELOAD from the initramfs.
excluded_preload_file='/usr/lib/systemd/system.conf.d/40-hardened_malloc.conf'
tmp_preload_file=$(mktemp --tmpdir '40-hardened_malloc-XXXXXXXXXX.conf')
mv -- "${excluded_preload_file}" "${tmp_preload_file}"
trap 'mv -- "${tmp_preload_file}" "${excluded_preload_file}"' EXIT

# Temporarily patch /etc/os-release to avoid the initramfs depending on the
# version number (which changes daily).
tmp_release_file=$(mktemp --tmpdir 'os-release-XXXXXXXXXX')
cp -- /etc/os-release "${tmp_release_file}"
sed -Ei --follow-symlinks -e '/^(OSTREE_)?VERSION=/d' /etc/os-release
trap 'cp -- "${tmp_release_file}" /etc/os-release; rm -f -- "${tmp_release_file}"' EXIT

qualified_kernel=$(rpm -q 'kernel' --qf='%{VERSION}-%{RELEASE}.%{ARCH}')

# Ensure all architecture-specific variants of libhardened_malloc.so are
# included, not just the one for the build system CPU's microarchitecture.
extra_files=(
    /usr/lib64/libhardened_malloc.so
    /usr/lib64/glibc-hwcaps/*/libhardened_malloc.so
)

/usr/bin/dracut \
    --kver "${qualified_kernel}" \
    --force \
    --add 'ostree' \
    --install "${extra_files[*]}" \
    --no-hostonly \
    --reproducible \
    "/usr/lib/modules/${qualified_kernel}/initramfs.img"

chmod 0600 "/usr/lib/modules/${qualified_kernel}/initramfs.img"
