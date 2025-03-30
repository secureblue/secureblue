#!/usr/bin/env bash

set -oue pipefail

echo "Disabling the modem manager"
systemctl disable ModemManager
systemctl mask ModemManager
