#!/usr/bin/env bash

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