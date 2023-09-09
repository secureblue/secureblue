#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

cp -r "$BLING_DIRECTORY/files/usr/etc/systemd/system/dconf-update.service" "/usr/etc/systemd/system/dconf-update.service"
systemctl enable dconf-update.services