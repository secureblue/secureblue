#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025 Universal Blue
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -oue pipefail

# We never use this repo, so remove it early to prevent failed calls to it
rm -f /etc/yum.repos.d/fedora-cisco-openh264.repo

install_repo() {
  versioned_repo="${1//%OS_VERSION%/43}"
  curl -fLsS --retry 5 -o "/etc/yum.repos.d/${versioned_repo##*/}" "$versioned_repo"
}

common_repos=(
  "https://copr.fedorainfracloud.org/coprs/secureblue/crane/repo/fedora-%OS_VERSION%/secureblue-crane-fedora-%OS_VERSION%.repo"
  "https://copr.fedorainfracloud.org/coprs/secureblue/slsa-verifier/repo/fedora-%OS_VERSION%/secureblue-slsa-verifier-fedora-%OS_VERSION%.repo"
  "https://copr.fedorainfracloud.org/coprs/secureblue/no_rlimit_as/repo/fedora-%OS_VERSION%/secureblue-no_rlimit_as-fedora-%OS_VERSION%.repo"
  "https://copr.fedorainfracloud.org/coprs/secureblue/hardened_malloc/repo/fedora-%OS_VERSION%/secureblue-hardened_malloc-fedora-%OS_VERSION%.repo"
  "https://copr.fedorainfracloud.org/coprs/secureblue/run0edit/repo/fedora-%OS_VERSION%/secureblue-run0edit-fedora-%OS_VERSION%.repo"
  "https://negativo17.org/repos/fedora-multimedia.repo"
)

desktop_repos=(
  "https://copr.fedorainfracloud.org/coprs/secureblue/bubblejail/repo/fedora-%OS_VERSION%/secureblue-bubblejail-fedora-%OS_VERSION%.repo"
  "https://copr.fedorainfracloud.org/coprs/secureblue/branding/repo/fedora-%OS_VERSION%/secureblue-branding-fedora-%OS_VERSION%.repo"
  "https://copr.fedorainfracloud.org/coprs/secureblue/homebrew/repo/fedora-%OS_VERSION%/secureblue-homebrew-fedora-%OS_VERSION%.repo"
)

server_repos=(
  "https://pkgs.tailscale.com/stable/fedora/tailscale.repo"
)

for repo in "${common_repos[@]}"; do
  install_repo "$repo"
done

if [[ "$IMAGE_NAME" == *"iot"* || "$IMAGE_NAME" == *"securecore"* ]]; then
  for repo in "${server_repos[@]}"; do
    install_repo "$repo"
  done
else
  for repo in "${desktop_repos[@]}"; do
    install_repo "$repo"
  done
fi
