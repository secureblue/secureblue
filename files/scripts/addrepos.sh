#!/usr/bin/env bash

# Copyright 2025 Universal Blue
# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

set -oue pipefail

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
  "https://copr.fedorainfracloud.org/coprs/secureblue/selinux-policy/repo/fedora-%OS_VERSION%/secureblue-selinux-policy-fedora-%OS_VERSION%.repo"
  "https://negativo17.org/repos/fedora-multimedia.repo"
)

desktop_repos=(
  "https://copr.fedorainfracloud.org/coprs/secureblue/bubblejail/repo/fedora-%OS_VERSION%/secureblue-bubblejail-fedora-%OS_VERSION%.repo"
  "https://copr.fedorainfracloud.org/coprs/secureblue/branding/repo/fedora-%OS_VERSION%/secureblue-branding-fedora-%OS_VERSION%.repo"
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
