#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

brewimport='import "/usr/share/ublue-os/just/50-brew.just"'

if ! grep -qF "$brewimport" /usr/share/ublue-os/justfile; then
    echo "$brewimport" >> /usr/share/ublue-os/justfile
fi
