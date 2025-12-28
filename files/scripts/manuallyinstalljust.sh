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

latest_url=$(curl -fLsS --retry 5 -o /dev/null -w '%{url_effective}' https://github.com/casey/just/releases/latest)
ver=$(basename "$latest_url")
temp_dir=$(mktemp -d)
curl -fLsS --retry 5 --create-dirs \
    "https://github.com/casey/just/releases/download/${ver}/just-${ver}-${OS_ARCH}-unknown-linux-musl.tar.gz" -o "${temp_dir}/just-${ver}-${OS_ARCH}-unknown-linux-musl.tar.gz" \
    "https://github.com/casey/just/releases/download/${ver}/SHA256SUMS" -o "${temp_dir}/SHA256SUMS"
cd "${temp_dir}"
if ! sha256sum -c SHA256SUMS --ignore-missing; then
    echo "Just tarball verification FAILED! Exiting..."
    exit 1
fi
cd -
mkdir "${temp_dir}/just"
tar -xzf "${temp_dir}/just-${ver}-${OS_ARCH}-unknown-linux-musl.tar.gz" -C "${temp_dir}/just/"
cp "${temp_dir}/just/just" /usr/bin/just
chmod 0755 /usr/bin/just
cp "${temp_dir}/just/completions/just.bash" /usr/share/bash-completion/completions/just
cp "${temp_dir}/just/just.1" /usr/share/man/man1/just.1
rm -r "${temp_dir}"
