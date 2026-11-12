#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail
shopt -s nullglob

dnf install python3-dnf -y

secureblue_gpg_key_path="$(dnf repo info secureblue --json | jq -r '.[0].gpg_key.[0]')"
rpmkeys --import "${secureblue_gpg_key_path}"

# Package signatures are NOT being checked at this stage,
# see https://github.com/rpm-software-management/dnf5/issues/1985
dnf --best --repo=secureblue -y download trivalent

trivalent_rpms_found=0
for trivalent_rpm in trivalent-[0-9]*."${OS_ARCH}".rpm; do
    ((++trivalent_rpms_found))
done

if ((trivalent_rpms_found == 1)); then
    echo "Trivalent RPM: ${trivalent_rpm}"
else
    echo "Number of Trivalent RPMs not one, found: ${trivalent_rpms_found}"
    exit 1
fi

trivalent_rpm_sans_prefix=${trivalent_rpm#trivalent-}
trivalent_version=${trivalent_rpm_sans_prefix%".${OS_ARCH}.rpm"}

provenance_file='provenance.intoto.json'
curl -fLsS --retry 5 -O "https://github.com/secureblue/Trivalent/releases/download/${trivalent_version}-${OS_ARCH}/${provenance_file}"

# Manually installing slsa-verifier from the release is a temporary measure
# until we ship the new slsa-verifier as an RPM package.
VERIFIER_VERSION="v0.1.1"
if [[ "${OS_ARCH}" == x86_64 ]]; then
    VERIFIER_ARCH=amd64
    VERIFIER_SHA256=7053bb00052a64c77dbba4400636fd22d336c1b10aba9aac1db44744b9efba31
else
    VERIFIER_ARCH=arm64
    VERIFIER_SHA256=b46cbbdf75a0ea3a5595b1bb8fc9b3a8c5590f80017d4e7fb0d05fb471229b0d
fi

VERIFIER="slsa-verifier-${VERIFIER_VERSION}-linux-${VERIFIER_ARCH}"
curl -fLsS --retry 5 -O "https://github.com/slsa-framework/verifier/releases/download/${VERIFIER_VERSION}/${VERIFIER}"
echo "${VERIFIER_SHA256}  ${VERIFIER}" | sha256sum --check
chmod +x "${VERIFIER}"

"./${VERIFIER}" build "${provenance_file}" "${trivalent_rpm}" \
    --level 3 \
    --require-signatures \
    --signer 'sigstore(identityMatch=regex)::https://token.actions.githubusercontent.com::https://github\.com/slsa-framework/actions/\.github/workflows/attest_actions\.yml@refs/tags/v[0-9]+\.[0-9]+\.[0-9]+' \
    --param 'expected_source:github.com/secureblue/Trivalent' \
    --param 'expected_branch:live' \
    --param 'trusted_builders:[https://github.com/secureblue/Trivalent/.github/workflows/build_x86_64.yml@refs/heads/live,https://github.com/secureblue/Trivalent/.github/workflows/build_aarch64.yml@refs/heads/live]'

rm "${VERIFIER}" "${provenance_file}"

# Forcing GPG check for packages installed outside of a repository
dnf --setopt=localpkg_gpgcheck=True --setopt=install_weak_deps=False -y install "${trivalent_rpm}"

sed -i 's/org\.mozilla\.firefox\.desktop/trivalent.desktop/' /usr/share/applications/mimeapps.list
