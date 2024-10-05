#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

echo "Disabling the modem manager"
systemctl disable ModemManager
systemctl mask ModemManager
