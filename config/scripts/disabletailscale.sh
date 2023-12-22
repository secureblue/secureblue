#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

echo "Disabling tailscale"
systemctl disable tailscaled
systemctl mask tailscaled
