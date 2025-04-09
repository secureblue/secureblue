#!/usr/bin/env bash

set -oue pipefail

echo "Disabling tailscale"
systemctl disable tailscaled
systemctl mask tailscaled
