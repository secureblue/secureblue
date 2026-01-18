#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -oue pipefail

QUALIFIED_KERNEL="$(rpm -qa | grep -P 'kernel-(\d+\.\d+\.\d+)' | sed 's/kernel-//')"

temp_conf_file="$(mktemp '/etc/dracut.conf.d/zzz-loglevels-XXXXXXXXXX.conf')"
cat >"${temp_conf_file}" <<'EOF'
stdloglvl=4
sysloglvl=0
kmsgloglvl=0
fileloglvl=0
EOF

excluded_preload_file='/usr/lib/systemd/system.conf.d/40-hardened_malloc.conf'
tmp_preload_file='/tmp/40-hardened_malloc.conf'

mv "${excluded_preload_file}" "${tmp_preload_file}"

/usr/bin/dracut \
    --kver "${QUALIFIED_KERNEL}" \
    --force \
    --add 'ostree' \
    --no-hostonly \
    --reproducible \
    "/lib/modules/${QUALIFIED_KERNEL}/initramfs.img"

mv "${tmp_preload_file}" "${excluded_preload_file}"

rm -- "${temp_conf_file}"

chmod 0600 "/lib/modules/${QUALIFIED_KERNEL}/initramfs.img"
