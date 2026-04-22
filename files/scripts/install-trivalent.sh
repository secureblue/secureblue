#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail
shopt -s nullglob

ARCH="$(uname -m)"

dnf install python3-dnf -y

secureblue_gpg_key_path="$(dnf repo info secureblue --json | jq -r '.[0].gpg_key.[0]')"
rpmkeys --import "${secureblue_gpg_key_path}"

# Package signatures are NOT being checked at this stage,
# see https://github.com/rpm-software-management/dnf5/issues/1985
dnf --best --repo=secureblue -y download trivalent

trivalent_rpms_found=0
for trivalent_rpm in trivalent-[0-9]*."${ARCH}".rpm; do
    (( ++trivalent_rpms_found ))
done

if (( trivalent_rpms_found == 1 )); then
    echo "Trivalent RPM: ${trivalent_rpm}"
else
    echo "Number of Trivalent RPMs not one, found: ${trivalent_rpms_found}"
    exit 1
fi

trivalent_rpm_sans_prefix=${trivalent_rpm#trivalent-}
trivalent_version=${trivalent_rpm_sans_prefix%".${ARCH}.rpm"}

trivalent_selinux_pkg="trivalent-selinux-${trivalent_version}"
dnf --repo=secureblue -y download "${trivalent_selinux_pkg}"

trivalent_selinux_rpm="${trivalent_selinux_pkg}.noarch.rpm"

if [[ -f "${trivalent_selinux_rpm}" ]]; then
    echo "Trivalent SELinux policy RPM: ${trivalent_selinux_rpm}"
else
    echo "trivalent-selinux RPM not found"
    exit 1
fi

provenance_file="multiple.intoto.jsonl"
curl -fLsS --retry 5 -O "https://github.com/secureblue/Trivalent/releases/download/${trivalent_version}/${provenance_file}"

slsa-verifier verify-artifact \
    --provenance-path "${provenance_file}" \
    --source-uri 'github.com/secureblue/Trivalent' \
    --source-branch 'live' \
    "${trivalent_rpm}" "${trivalent_selinux_rpm}"

# Forcing GPG check for packages installed outside of a repository
dnf --setopt=localpkg_gpgcheck=True --setopt=install_weak_deps=False -y \
    install "${trivalent_rpm}" "${trivalent_selinux_rpm}"

sed -i 's/org\.mozilla\.firefox\.desktop/trivalent.desktop/' /usr/share/applications/mimeapps.list
