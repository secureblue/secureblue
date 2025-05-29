#!/usr/bin/env bash

set -oue pipefail

# Copyright 2025 fiftydinar
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
LATEST_URL="$(curl -Ls -o /dev/null -w '%{url_effective}' https://github.com/casey/just/releases/latest)"
VER="$(basename "$LATEST_URL")"
curl -fLs --create-dirs "https://github.com/casey/just/releases/download/${VER}/just-${VER}-x86_64-unknown-linux-musl.tar.gz" -o "/tmp/just-${VER}-x86_64-unknown-linux-musl.tar.gz"
curl -fLs --create-dirs "https://github.com/casey/just/releases/download/${VER}/SHA256SUMS" -o /tmp/SHA256SUMS
cd /tmp
if ! sha256sum -c SHA256SUMS --ignore-missing
then
    echo "Just tarball verification FAILED! Exiting..."
    exit 1
fi
cd -
mkdir -p /tmp/just && tar -xzf "/tmp/just-${VER}-x86_64-unknown-linux-musl.tar.gz" -C /tmp/just/
cp /tmp/just/just /usr/bin/just && chmod 0755 /usr/bin/just
cp /tmp/just/completions/just.bash /usr/share/bash-completion/completions/just
rm "/tmp/just-${VER}-x86_64-unknown-linux-musl.tar.gz"
rm -r /tmp/just/