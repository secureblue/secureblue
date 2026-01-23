#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -oue pipefail

ARCH="$(uname -m)"

dnf install python3-dnf -y

curl -fLsS --retry 5 -o /etc/yum.repos.d/repo.secureblue.dev.secureblue.repo https://repo.secureblue.dev/secureblue.repo
secureblue_gpg_key_path="$(dnf repo info secureblue --json | jq -r '.[0].gpg_key.[0]')"
rpmkeys --import "${secureblue_gpg_key_path}"

# The package signature is NOT being checked at this stage,
# see https://github.com/rpm-software-management/dnf5/issues/1985
dnf --best --repo=secureblue -y download trivalent

trivalent_rpms_found=0
for trivalent_rpm in trivalent-*."${ARCH}".rpm; do
    (( ++trivalent_rpms_found ))
done

if [ "$trivalent_rpms_found" -eq 1 ]; then
    echo "Found: ${trivalent_rpms_found}"
else
    echo "Number of trivalent rpms not one, found: ${trivalent_rpms_found}"
    exit 1
fi

trivalent_rpm_sans_prefix=${trivalent_rpm#trivalent-}
trivalent_version=${trivalent_rpm_sans_prefix%".${ARCH}.rpm"}

provenance_file="${trivalent_rpm}.intoto.jsonl"
wget "https://github.com/secureblue/Trivalent/releases/download/${trivalent_version}/${provenance_file}"

slsa-verifier verify-artifact "${trivalent_rpm}" --provenance-path "${provenance_file}" --source-uri github.com/secureblue/Trivalent --source-branch live

# Forcing GPG check for a package installed outside of a repository
dnf --setopt=localpkg_gpgcheck=True -y install "${trivalent_rpm}"

sed -i 's/org\.mozilla\.firefox\.desktop/trivalent.desktop/' /usr/share/applications/mimeapps.list
