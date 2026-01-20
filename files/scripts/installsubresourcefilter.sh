#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

echo '
[copr:copr.fedorainfracloud.org:secureblue:trivalent]
name=Copr repo for trivalent owned by secureblue
baseurl=https://download.copr.fedorainfracloud.org/results/secureblue/trivalent/fedora-$releasever-x86_64/
type=rpm-md
skip_if_unavailable=True
gpgcheck=1
gpgkey=https://download.copr.fedorainfracloud.org/results/secureblue/trivalent/pubkey.gpg
repo_gpgcheck=0
enabled=1
enabled_metadata=1
' > /etc/yum.repos.d/secureblue-trivalent-fedora-43.repo

dnf install -y --setopt=install_weak_deps=False trivalent-subresource-filter

rm -f /etc/yum.repos.d/secureblue-trivalent-fedora-43.repo