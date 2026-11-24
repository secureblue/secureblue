#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

KERNEL_VERSION="$(rpm -q 'kernel' --queryformat '%{VERSION}-%{RELEASE}.%{ARCH}')"

dnf --best --repo=secureblue -y download \
    "kernel-devel-${KERNEL_VERSION}" \
    "kernel-devel-matched-${KERNEL_VERSION}"

provenance_file='provenance.intoto.json'
curl -fLsS --retry 5 -O "https://github.com/secureblue/kernel/releases/download/${KERNEL_VERSION%.fc*}/${provenance_file}"

slsa-verifier build "${provenance_file}" ./kernel-devel-*.rpm \
    --level 3 \
    --require-signatures \
    --signer 'sigstore(identityMatch=regex)::https://token.actions.githubusercontent.com::https://github\.com/slsa-framework/actions/\.github/workflows/attest_actions\.yml@refs/tags/v[0-9]+\.[0-9]+\.[0-9]+' \
    --param 'expected_source:github.com/secureblue/kernel' \
    --param 'expected_branch:live' \
    --param 'trusted_builders:[https://github.com/secureblue/kernel/.github/workflows/kernel-build.yml@refs/heads/live]'

rm "${provenance_file}"

dnf --setopt=localpkg_gpgcheck=True --setopt=install_weak_deps=False --disable-repo=secureblue -y install ./kernel-devel-*.rpm

rm ./kernel-devel-*.rpm
