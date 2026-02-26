#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# Set dracut log levels using temporary configuration file.
# This avoids logging messages to the system journal, which can significantly
# impact performance in the default configuration.
temp_conf_file=$(mktemp '/etc/dracut.conf.d/zzz-loglevels-XXXXXXXXXX.conf')
cat >"${temp_conf_file}" <<'EOF'
stdloglvl=4
sysloglvl=0
kmsgloglvl=0
fileloglvl=0
EOF

# Exclude file that sets LD_PRELOAD from the initramfs.
excluded_preload_file='/usr/lib/systemd/system.conf.d/40-hardened_malloc.conf'
tmp_preload_file=$(mktemp --tmpdir '40-hardened_malloc-XXXXXXXXXX.conf')
mv "${excluded_preload_file}" "${tmp_preload_file}"

# Temporarily patch /etc/os-release to avoid the initramfs depending on the
# version number (which changes daily).
tmp_release_file=$(mktemp --tmpdir 'os-release-XXXXXXXXXX')
cp /etc/os-release "${tmp_release_file}"
sed -Ei -e '/^(OSTREE_)VERSION=/d' /etc/os-release

qualified_kernel=$(rpm -qa | grep -oP 'kernel-\K\d+\.\d+\.\d+.*')

/usr/bin/dracut \
    --kver "${qualified_kernel}" \
    --force \
    --add 'ostree' \
    --no-hostonly \
    --reproducible \
    "/usr/lib/modules/${qualified_kernel}/initramfs.img"

# Restore temporarily modified files
mv "${tmp_preload_file}" "${excluded_preload_file}"
cp "${tmp_release_file}" /etc/os-release

rm "${tmp_release_file}" "${temp_conf_file}"

chmod 0600 "/usr/lib/modules/${qualified_kernel}/initramfs.img"
