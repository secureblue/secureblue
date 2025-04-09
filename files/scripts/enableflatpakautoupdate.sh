#!/usr/bin/env bash

set -oue pipefail

systemctl --global enable flatpak-user-update.timer
systemctl enable flatpak-system-update.timer