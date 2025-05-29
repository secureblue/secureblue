#!/usr/bin/env bash

set -oue pipefail

VER=$(basename $(curl -Ls -o /dev/null -w %{url_effective} https://github.com/casey/just/releases/latest))
curl -fLs --create-dirs https://github.com/casey/just/releases/download/${VER}/just-${VER}-x86_64-unknown-linux-musl.tar.gz -o /tmp/just-${VER}-x86_64-unknown-linux-musl.tar.gz
curl -fLs --create-dirs https://github.com/casey/just/releases/download/${VER}/SHA256SUMS -o /tmp/SHA256SUMS
ORIGINAL_WD=$(pwd)
cd /tmp
if ! sha256sum -c SHA256SUMS --ignore-missing
then
    echo "Just tarball verification FAILED! Exiting..."
    exit 1
fi
cd $ORIGINAL_WD
mkdir -p /tmp/just && tar -xzf /tmp/just-${VER}-x86_64-unknown-linux-musl.tar.gz -C /tmp/just/
cp /tmp/just/just /usr/bin/just && chmod 0755 /usr/bin/just
cp /tmp/just/completions/just.bash /usr/share/bash-completion/completions/just
rm /tmp/just-x86_64-unknown-linux-musl.tar.gz
rm -r /tmp/just/