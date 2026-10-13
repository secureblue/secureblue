#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# This is a noarch package that we only build on x86_64, for both arches. As such, this is
# hardcoded to x86_64 deliberately.
dnf install -y --setopt=install_weak_deps=False \
    --repo=copr:copr.fedorainfracloud.org:secureblue:packages \
    --setopt='copr:copr.fedorainfracloud.org:secureblue:packages.baseurl=https://download.copr.fedorainfracloud.org/results/secureblue/packages/fedora-$releasever-x86_64/' \
    trivalent-subresource-filter
