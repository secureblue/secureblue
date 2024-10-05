#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

echo "Disabling the alsa state daemon"
systemctl disable alsa-state
systemctl mask alsa-state
