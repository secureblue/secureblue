#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# This is a noarch package that we only build on x86_64, for both arches. As such, this is
# hardcoded to x86_64 deliberately.
temp_repo_file=$(mktemp --tmpdir 'tmp-XXXXXXXXXX.repo')
cat <<'EOF' >"${temp_repo_file}"
[copr:copr.fedorainfracloud.org:secureblue:packages-x86_64]
name=Copr repo for trivalent owned by secureblue
baseurl=https://download.copr.fedorainfracloud.org/results/secureblue/packages/fedora-$releasever-x86_64/
type=rpm-md
skip_if_unavailable=True
gpgcheck=1
gpgkey=file:///usr/share/pki/rpm-gpg/secureblue-copr-pubkey.gpg
repo_gpgcheck=0
enabled=1
enabled_metadata=1
priority=1
EOF

dnf install -y --setopt=install_weak_deps=False \
    --repofrompath="copr:copr.fedorainfracloud.org:secureblue:packages-x86_64,${temp_repo_file}" \
    --repo=copr:copr.fedorainfracloud.org:secureblue:packages-x86_64 \
    trivalent-subresource-filter

rm -f "${temp_repo_file}"
