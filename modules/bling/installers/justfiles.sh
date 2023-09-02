#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

cp -r "$BLING_DIRECTORY"/files/usr/share/ublue-os/just/* "/usr/share/ublue-os/just"