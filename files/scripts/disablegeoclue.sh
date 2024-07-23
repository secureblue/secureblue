#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

echo "Disabling the location service"
systemctl disable geoclue
systemctl mask geoclue
