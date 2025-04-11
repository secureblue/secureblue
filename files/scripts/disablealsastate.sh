#!/usr/bin/env bash

set -oue pipefail

echo "Disabling the alsa state daemon"
systemctl disable alsa-state
systemctl mask alsa-state
