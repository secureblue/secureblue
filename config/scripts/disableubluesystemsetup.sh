#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

echo "Disabling ublue-system-setup"
systemctl disable ublue-system-setup
systemctl mask ublue-system-setup
