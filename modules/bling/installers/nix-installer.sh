#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

cp "$BLING_DIRECTORY/files/usr/bin/ublue-nix-install" "/usr/bin/ublue-nix-install"
cp "$BLING_DIRECTORY/files/usr/bin/ublue-nix-uninstall" "/usr/bin/ublue-nix-uninstall"