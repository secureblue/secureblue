#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

if [[ "$IMAGE_NAME" == *"main"* ]]; then
    systemctl disable switcheroo-control.service
    systemctl mask switcheroo-control.service
fi