#!/usr/bin/env bash

set -oue pipefail

echo "Disabling the location service"
systemctl disable geoclue
systemctl mask geoclue
