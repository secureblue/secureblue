#!/usr/bin/env bash

set -oue pipefail

echo "Disabling print services"
systemctl disable cups
systemctl mask cups

systemctl disable cups-browsed
systemctl mask cups-browsed
