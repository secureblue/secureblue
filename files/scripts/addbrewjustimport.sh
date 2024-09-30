#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail
echo '

import "/usr/share/ublue-os/just/50-brew.just"

' >> /usr/share/ublue-os/justfile
